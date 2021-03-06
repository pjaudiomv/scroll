# scroll
In its present form, scroll is a python-based command line utility for generating meeting list PDFs from [tomato](https://github.com/jbraswell/tomato). In the future, scroll will be a full-featured website for generating meeting list PDFs.

## Installation
Scroll requires Python 3, [requests](http://docs.python-requests.org/en/master/), and [pyfpdf](https://github.com/reingart/pyfpdf).

1. [Install python](https://www.python.org/downloads/)
2. [Install pip](https://pip.pypa.io/en/stable/installing/)
3. Install requests: `pip3 install requests`
4. Install pyfpdf: `pip3 install fpdf`

No effort has been made to create a proper pypi package for scroll, so you'll need to clone this repository. After cloning, you can run `scroll.py` with `python3`. See the examples below.
 
## Usage
```
[jbraswell@localhost src]$ python3 scroll.py --help
usage: scroll [-h] [--recursive] [--main-header-field {weekday,city}]
              [--second-header-field {weekday,city}] [--bookletize]
              [--time-column-width TIME_COLUMN_WIDTH]
              [--duration-column-width DURATION_COLUMN_WIDTH]
              [--meeting-font {arial,helvetica,courier,times}]
              [--meeting-font-size MEETING_FONT_SIZE]
              [--header-font {arial,helvetica,courier,times}]
              [--header-font-size HEADER_FONT_SIZE]
              service_body_ids {letter,legal,tabloid} output_file

positional arguments:
  service_body_ids      Comma-separated list of service body ids. Scroll will
                        retrieve the meetings for these service bodies from
                        tomato
  {letter,legal,tabloid}
                        The paper size you intend to use when printing the PDF
  output_file           The path to the PDF file generated by scroll

optional arguments:
  -h, --help            show this help message and exit
  --recursive           If set, all meetings belonging to child service bodies
                        of the specified service_body_ids will be included
  --main-header-field {weekday,city}
                        The primary header field to use when generating the
                        PDF. Defaults to weekday
  --second-header-field {weekday,city}
                        The secondary header field to use when generating the
                        PDF. Defaults to none
  --bookletize          For use with printers without a 'booklet' option. Two
                        booklet pages per PDF page
  --time-column-width TIME_COLUMN_WIDTH
                        The width, in mm, of the meeting start time column.
                        Defaults to 15
  --duration-column-width DURATION_COLUMN_WIDTH
                        The width, in mm, of the meeting duration column.
                        Defaults to 15
  --meeting-font {arial,helvetica,courier,times}
                        The font used for each meeting. Defaults to arial
  --meeting-font-size MEETING_FONT_SIZE
                        The font size used for each meeting. Defaults to 10
  --header-font {arial,helvetica,courier,times}
                        The font used for headers. Defaults to arial
  --header-font-size HEADER_FONT_SIZE
                        The font size used for headers. Defaults to 10
```

## Examples
#### Example 1
Generate test.pdf, targeting the letter paper size, for service bodies 753 and 751
```
[jbraswell@localhost src]$ python3 scroll.py 753,751 letter test.pdf
```
Output: [test.pdf](https://github.com/jbraswell/scroll/blob/master/example_1.pdf)

#### Example 2
Generate test.pdf, targeting the letter paper size, for service body 762 and its children
```
$ python3 scroll.py 762 letter test.pdf --recursive
```
Output: [test.pdf](https://github.com/jbraswell/scroll/blob/master/example_2.pdf)

#### Example 3
Generate test.pdf, targeting the letter paper size, for service bodies 753 and 751, customizing the meeting font
```
$ python3 scroll.py 753,751 letter test.pdf --meeting-font=times
```
Output: [test.pdf](https://github.com/jbraswell/scroll/blob/master/example_3.pdf)

#### Example 4
Generate test.pdf, targeting the letter paper size, for service body 762 and its children, adding secondary 'city' headers, changing font sizes to 8, changing the width of the time and duration columns
```
$ python3 scroll.py 762 letter test.pdf \
    --recursive \
    --main-header-field=weekday \
    --second-header-field=city \
    --meeting-font-size=8 \
    --header-font-size=8 \
    --time-column-width=12 \
    --duration-column-width=10
```
Output: [test.pdf](https://github.com/jbraswell/scroll/blob/master/example_4.pdf)

#### Example 5
Generate test.pdf, same as previous, but bookletized
```
$ python3 scroll.py 762 letter test.pdf \
    --recursive \
    --bookletize \
    --main-header-field=weekday \
    --second-header-field=city \
    --meeting-font-size=8 \
    --header-font-size=8 \
    --time-column-width=12 \
    --duration-column-width=10
```
Output: [test.pdf](https://github.com/jbraswell/scroll/blob/master/example_5.pdf)