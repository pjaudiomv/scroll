cd src
echo "Generating example 1"
python3 scroll.py 2466,1207,1208 letter ../example_1.pdf
echo "Generating example 2"
python3 scroll.py 1215 letter ../example_2.pdf --recursive
echo "Generating example 3"
python3 scroll.py 2466,1207,1208 letter ../example_3.pdf --meeting-font=times
echo "Generating example 4"
python3 scroll.py 1215 letter ../example_4.pdf --recursive --main-header-field=weekday --second-header-field=city --meeting-font-size=8 --header-font-size=8 --time-column-width=12 --duration-column-width=10
echo "Generating example 5"
python3 scroll.py 1215 letter ../example_5.pdf --recursive --bookletize --main-header-field=weekday --second-header-field=city --meeting-font-size=8 --header-font-size=8 --time-column-width=12 --duration-column-width=10
echo "Generating example 6"
python3 scroll.py 1215 letter ../example_6.pdf --recursive --bookletize --main-header-field=weekday --second-header-field=city --meeting-font-size=8 --header-font-size=8 --time-column-width=12 --duration-column-width=10 --exclude-qr-codes
cd ..
