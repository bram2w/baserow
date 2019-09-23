install-dependencies:
	curl -sL https://deb.nodesource.com/setup_10.x | bash
	apt-get install -y nodejs

	curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
	echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
	apt-get update && apt-get install -y yarn

	yarn install

eslint:
	yarn run eslint || exit;

stylelint:
	yarn run stylelint || exit;

lint: eslint stylelint

jest:
	yarn run jest || exit;

test: jest
