Thank you for wanting to contribute to OpenFisca-France-Data! :smiley:

TL;DR: [GitHub Flow](https://guides.github.com/introduction/flow/), [SemVer](http://semver.org/), sweat on naming and messages.


## Pull requests

We follow the [GitHub Flow](https://guides.github.com/introduction/flow/): all code contributions are submitted via a pull request towards the `master` branch.

Opening a Pull Request means you want that code to be merged. If you want to only discuss it, send a link to your branch along with your questions through whichever communication channel you prefer.


### Peer reviews

All pull requests must be reviewed by someone else than their original author.

> In case of a lack of available reviewers, one may review oneself, but only after at least 24 hours have passed without working on the code to review.

To help reviewers, make sure to add to your PR a **clear text explanation** of your changes.

In case of breaking changes, you **must** give details about what features were deprecated.

> You must also provide guidelines to help users adapt their code to be compatible with the new version of the package.


## Advertising changes

### Version number

Use `make bump` to bump the version number.

We follow the [semantic versioning](http://semver.org/) spec: any change impacts the version number, and the version number conveys API compatibility information **only**.

Examples:

#### Patch bump

- Internal optimization, with no consequence to the package's API.

#### Minor bump

- Adding a helper.

#### Major bump

- Renaming or deprecating a helper.
- Changing the signature or behaviour of a helper.


### Changelog

Document all changes in the `CHANGELOG.md` file, following the examples already there.
