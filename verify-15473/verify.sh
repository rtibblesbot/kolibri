#!/usr/bin/env bash
# Exercise deploy_pages.yml against a stand-in of the live installer-debian site.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
WF="$HERE/deploy_pages.yml"
T=$(mktemp -d)
cd "$T"

new_key() {
  local home
  home=$(mktemp -d)
  GNUPGHOME=$home gpg --batch --passphrase '' --quick-gen-key "$1 <cutover@example.com>" rsa3072 sign never 2>/dev/null
  GNUPGHOME=$home gpg --list-secret-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}' > "$1.fpr"
  GNUPGHOME=$home gpg --batch --armor --export-secret-keys > "$1.sec"
  GNUPGHOME=$home gpg --batch --export > "$1.gpg"
  echo "$home"
}
OLD_HOME=$(new_key old)
new_key wrong > /dev/null
OLD_FPR=$(cat old.fpr)

# Stand-in for the live site: upstream gh-pages, re-signed with the ephemeral key.
git clone -q --depth 1 -b gh-pages https://github.com/learningequality/kolibri-installer-debian site
rm -rf site/.git
sed -i "s/^SignWith: .*/SignWith: $OLD_FPR/" site/conf/distributions
GNUPGHOME=$OLD_HOME reprepro -b site export stable
cp -a site site-orig
(cd site && python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null 2>&1 &)

# Synthetic cutover .deb over GitHub's 100 MiB push limit.
mkdir -p pkg/DEBIAN pkg/usr/share/kolibri-cutovertest debsrv
head -c 110M /dev/urandom > pkg/usr/share/kolibri-cutovertest/pad
cat > pkg/DEBIAN/control <<EOF
Package: kolibri
Version: 0.19.5+cutovertest1
Architecture: all
Maintainer: Cutover Test <cutover@example.com>
Description: cutover test
EOF
dpkg-deb -Znone --build pkg debsrv/kolibri_0.19.5+cutovertest1_all.deb
(cd debsrv && python3 -m http.server 8001 --bind 127.0.0.1 >/dev/null 2>&1 &)
sleep 2

export SITE_URL=http://127.0.0.1:8000
export DEB_URL=http://127.0.0.1:8001/kolibri_0.19.5+cutovertest1_all.deb
FAILS=0
fail() { echo "::error::$*"; FAILS=$((FAILS + 1)); }

run() { # <case> <secret-key-file> [workflow]
  echo "=== $1"
  DEBIAN_REPO_SIGNING_KEY=$(cat "$2") python3 "$HERE/run_workflow.py" "${3:-$WF}" site | tee "$1.log"
  return "${PIPESTATUS[0]}"
}

fields() { grep -E '^(Origin|Label|Suite|Codename):' "$1/dists/stable/Release"; }

served() { awk '/^Package:/ {p=$2} /^Version:/ {print p, $2}' site/dists/stable/main/binary-amd64/Packages | sort -u; }

assert_cutover_site() {
  gpgv --keyring "$T/old.gpg" site/dists/stable/InRelease || fail "$1: InRelease does not verify with the old key"
  diff <(fields site-orig) <(fields site) || fail "$1: Release fields changed"
  printf 'kolibri 0.19.5+cutovertest1\nkolibri 0.19.5-0ubuntu1\n' | diff - <(served) || fail "$1: served packages wrong"
  size=$(stat -c %s site/pool/main/k/kolibri/kolibri_0.19.5+cutovertest1_all.deb 2>/dev/null || echo 0)
  [ "$size" -gt $((100 * 1024 * 1024)) ] || fail "$1: >100 MiB .deb not served (size $size)"
}

if run wrong-key wrong.sec; then
  fail "wrong-key: run succeeded"
else
  grep -q '^FAILED_STEP=Record the packages the live site serves$' wrong-key.log || fail "wrong-key: failed at the wrong step"
fi
diff -rq site-orig site || fail "wrong-key: site changed"

run cutover old.sec || fail "cutover: run failed"
assert_cutover_site cutover

run redispatch old.sec || fail "redispatch: run failed"
assert_cutover_site redispatch

sed 's/^\( *\)Label: Kolibri$/\1Label: Kolibri Changed/' "$WF" > label.yml
grep -q 'Label: Kolibri Changed' label.yml || fail "label: could not mutate Label"
if run label old.sec label.yml; then
  fail "label: run succeeded with a changed Label"
else
  grep -q '^FAILED_STEP=Check the deployed site$' label.log || fail "label: failed at the wrong step"
fi

echo "FAILS=$FAILS"
[ "$FAILS" -eq 0 ]
