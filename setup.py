import pathlib
import setuptools



if __name__ == '__main__':

	packages = setuptools.find_packages(exclude = ['tests'])

	setuptools.setup(

		name                          = 'ruiner',
		version                       = '0.1.0',
		python_requires               = '>=3.11',
		keywords                      = ['template-engine'],
		url                           = 'https://github.com/MentalBlood/ruiner',

		description                   = 'Safe and clean template engine',
		long_description              = (pathlib.Path(__file__).parent / 'README.md').read_text(),
		long_description_content_type = 'text/markdown',

		classifiers                   = [
			'Development Status :: 5 - Production/Stable',
			'Intended Audience :: Developers',
			'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
			'Topic :: Text Processing :: Markup :: XML',
			'Topic :: Text Processing :: Markup :: HTML',
			'Typing :: Typed',
			'Operating System :: OS Independent',
			'Programming Language :: Python :: 3.11',
			'Programming Language :: Python :: 3.12',
			'License :: OSI Approved :: BSD License'
		],

		author                        = 'mentalblood',
		author_email                  = 'neceporenkostepan@gmail.com',
		maintainer                    = 'mentalblood',
		maintainer_email              = 'neceporenkostepan@gmail.com',

		packages                      = packages

	)
