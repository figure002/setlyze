from distutils.core import setup

setup (name='setlyze',
      version='0.1',
      description='A tool for analyzing SETL data.',
      long_description='A tool for analyzing SETL data.',
      author='Serrano Pereira',
      author_email='serrano.pereira@gmail.com',
      license='GPL3',
      platforms=['GNU/Linux','Windows'],
      scripts=['setlyze.pyw'],
      url='http://www.gimaris.com/setlyze/',
      packages=['setlyze', 'setlyze.analysis'],
      package_data={'setlyze': ['images/*.png']},
)
