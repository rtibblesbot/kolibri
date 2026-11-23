# -*- sh -*-
# Sourced as root by /etc/init.d/kolibri and the kolibri postinst after
# /etc/default/kolibri has set KOLIBRI_USER.

# util-linux 2.27's setpriv (Ubuntu 16.04) has no --ambient-caps; it was added in 2.31.
if setpriv --inh-caps +net_bind_service --ambient-caps +net_bind_service true 2>/dev/null
then
  run_as_kolibri_user() {
    HOME="$(getent passwd "$KOLIBRI_USER" | cut -d: -f6)" \
    SHELL="$(getent passwd "$KOLIBRI_USER" | cut -d: -f7)" \
    USER="$KOLIBRI_USER" \
    LOGNAME="$KOLIBRI_USER" \
    setpriv --reuid="$(id -u "$KOLIBRI_USER")" --regid="$(id -g "$KOLIBRI_USER")" --init-groups \
      --inh-caps +net_bind_service --ambient-caps +net_bind_service \
      /bin/sh -c "$1"
  }
else
  # Prefer runuser over su
  # See: https://github.com/learningequality/kolibri-installer-debian/issues/90
  # Check if runuser exists - it doesn't on 14.04
  if which runuser > /dev/null
  then
    SU_COMMAND="runuser"
  else
    SU_COMMAND="su"
  fi

  # We wanted this pattern, but it doesn't work on Ubuntu 14.04
  # because $HOME is unavailable when preserving the env with -p.
  #   su $KOLIBRI_USER -l -p -s /bin/sh -c "COMMAND"
  # However, this seems to preserve environment and switch $HOME
  # by default on both 14.04 and 16.04:
  #   su kolibri -c "COMMAND"
  run_as_kolibri_user() {
    $SU_COMMAND "$KOLIBRI_USER" -c "$1"
  }
fi
