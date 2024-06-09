:i count 3
:b shell 20
echo 'Hello, World!'
:i returncode 0
:b stdout 14
Hello, World!

:b stderr 0

:b shell 16
echo 'Foo, bar!'
:i returncode 0
:b stdout 10
Foo, bar!

:b stderr 0

:b shell 15
echo 'Ur, mom!'
:i returncode 0
:b stdout 9
Ur, mom!

:b stderr 0

