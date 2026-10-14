test(
    'kolibri-daemon stress',
    python_installation,
    args: [files('../stress_driver.py'), dbus_session_conf],
    env: tests_python_env,
    workdir: meson.current_source_dir(),
    timeout: 0
)
