## Running

### Setup env

```
python3 -m virtualenv env
env/bin/pip install -r requirements.txt
```

### Running

```
DATABASE_URL=postgres://<postgres-dsn> env/bin/python -m tokendirectory
```

## Running on heroku

### Config

#### Buildpacks

```
heroku buildpacks:add https://github.com/debitoor/ssh-private-key-buildpack.git
heroku buildpacks:add https://github.com/tristan/heroku-buildpack-pgsql-stunnel.git
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs

heroku config:set SSH_KEY=$(cat path/to/your/keys/id_rsa | base64)
```

#### Extra Config variables

```
heroku config:set PGSQL_STUNNEL_ENABLED=1
heroku config:set NODE_ENV=development
heroku config:set ID_SERVICE_URL=https://token-id-service.herokuapp.com
```

set cookie secret for login (should be something random and secret)

```
heroku config:set COOKIE_SECRET=<secret>
```

The `Procfile` and `runtime.txt` files required for running on heroku
are provided.

### Start

```
heroku ps:scale web:1
```

## Running tests

A convinience script exists to run all tests:
```
./run_tests.sh
```

To run a single test, use:

```
env/bin/python -m tornado.testing tokendirectory.test.<test-package>
```
