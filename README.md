# Cryptobot

# Design

- Consistency is the most important
- File and folder names lowercase
- Variable names snake_case
- Class names PascalCase

# Code Structuring

- Functions in Alphabetical order
- Separate code as much as possible

# To Do

 - Extended logging on exceptions, lines, file, etc...

## startup script
to fix startup.py script:
```s
$ mkdir -p ~/.docker/cli-plugins/
$ curl -SL https://github.com/docker/compose-cli/releases/download/v2.0.0-rc.1/docker-compose-linux-amd64 -o ~/.docker/cli-plugins/docker-compose
$ chmod +x ~/.docker/cli-plugins/docker-compose
```
https://github.com/docker/compose-cli/issues/2012