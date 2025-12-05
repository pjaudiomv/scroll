import datetime
import io
import qrcode
from fpdf import FPDF


weekdays = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
]


def get_key(d, key):
    try:
        return d[key]
    except KeyError:
        raise Exception('Key {} does not exist'.format(key))


def get_required_str(d, key):
    value = get_key(d, key)
    if not value:
        raise Exception('Missing required key {}'.format(key))
    return value


def get_int(d, key, valid_choices=None):
    try:
        value = int(get_key(d, key))
    except ValueError:
        raise Exception('Malformed {}'.format(key))
    if valid_choices and value not in valid_choices:
        raise Exception('Invalid {}'.format(key))
    return value


def get_time(d, key):
    try:
        value = get_key(d, key)
        if ':' not in value:
            # assume we're dealing with minutes
            value = int(value)
            if value < 60:
                value = '00:' + str(value)
            else:
                hours = int(value / 60)
                minutes = value % 60
                value = str(hours) + ':' + str(minutes)
        value = [int(t) for t in value.split(':')]
        value = datetime.time(*value)
        value.replace(tzinfo=datetime.timezone.utc)
        return value
    except ValueError:
        raise Exception('Malformed {}'.format(key))
    except TypeError:
        raise Exception('Malformed {}'.format(key), d)
    except:
        raise Exception('Unknown problem with {}'.format(key))


def get_timedelta(d, key):
    try:
        value = get_key(d, key)
        if ':' not in value:
            # assume we're dealing with minutes
            value = int(value)
            if value < 60:
                hours = 0
                minutes = str(value)
            else:
                hours = int(value / 60)
                minutes = value % 60
            return datetime.timedelta(hours=hours, minutes=minutes)
        else:
            value = [int(t) for t in value.split(':')]
            return datetime.timedelta(hours=value[0], minutes=value[1])
    except ValueError:
        raise Exception('Malformed {}'.format(key))
    except TypeError:
        raise Exception('Malformed {}'.format(key))
    except:
        raise Exception('Unknown problem with {}'.format(key))


class Meeting:
    def __init__(self, bmlt_object):
        self.name = self.replace_unicode_quotes(get_required_str(bmlt_object, 'meeting_name'))
        self.start_time = get_time(bmlt_object, 'start_time')
        self.duration = get_timedelta(bmlt_object, 'duration_time')
        self.weekday = get_int(bmlt_object, 'weekday_tinyint', valid_choices=[1, 2, 3, 4, 5, 6, 7])
        self.venue_type = int(bmlt_object.get('venue_type', 1))  # 1=in-person, 2=virtual, 3=hybrid
        self.virtual_meeting_link = self.replace_unicode_quotes(bmlt_object.get('virtual_meeting_link', ''))
        self.virtual_meeting_additional_info = self.replace_unicode_quotes(bmlt_object.get('virtual_meeting_additional_info', ''))
        self.phone_meeting_number = self.replace_unicode_quotes(bmlt_object.get('phone_meeting_number', ''))
        self.facility = self.replace_unicode_quotes(bmlt_object.get('location_text'))
        self.street = self.replace_unicode_quotes(bmlt_object.get('location_street'))
        self.city = self.replace_unicode_quotes(bmlt_object.get('location_municipality'))
        self.province = self.replace_unicode_quotes(bmlt_object.get('location_province'))
        self.postal_code = self.replace_unicode_quotes(bmlt_object.get('location_postal_code_1'))
        self.nation = self.replace_unicode_quotes(bmlt_object.get('nation'))
        self.formats = self.replace_unicode_quotes(bmlt_object.get('formats', ''))

    def replace_unicode_quotes(self, s):
        if not s:
            return s
        return s.replace("\u2018", "'").replace("\u2019", "'")

    @property
    def location(self):
        # Virtual-only meetings don't show location
        if self.venue_type == 2:
            return ''

        ret = ''
        if self.facility:
            ret += self.facility
        if self.street:
            ret = ret + ', ' if ret else ret
            ret += self.street
        if self.city:
            ret = ret + ', ' if ret else ret
            ret += self.city
        if self.province:
            ret = ret + ', ' if ret else ret
            ret += self.province
        if self.postal_code:
            ret = ret + ', ' if ret else ret
            ret += self.postal_code
        return ret


class PDFColumnEnd:
    pass


class PDFCoverPage:
    def __init__(self, service_bodies, formats, pdf_func, page_width, page_height):
        self.service_bodies = service_bodies if service_bodies else []
        self.formats = formats if formats else []
        self.pdf_func = pdf_func
        self.page_width = page_width
        self.page_height = page_height
    
    def write(self, pdf):
        """Write the cover page content."""
        # Save original margins
        left_margin = pdf.l_margin
        
        # Title
        pdf.set_font('Arial', 'B', 24)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(left_margin, 20)
        pdf.cell(self.page_width, h=15, txt='Meeting Schedule', border=0, ln=1, align='C')
        pdf.ln(h=5)
        
        # Generation date
        from datetime import datetime
        date_str = datetime.now().strftime('%B %d, %Y')
        pdf.set_font('Arial', '', 12)
        pdf.set_x(left_margin)
        pdf.cell(self.page_width, h=8, txt='Generated: ' + date_str, border=0, ln=1, align='C')
        pdf.ln(h=10)
        
        # Service bodies information
        if self.service_bodies:
            pdf.set_font('Arial', 'B', 14)
            pdf.set_x(left_margin)
            pdf.cell(self.page_width, h=8, txt='Service Bodies', border=0, ln=1, align='C')
            pdf.ln(h=5)
            
            for sb in self.service_bodies:
                pdf.set_x(left_margin)
                pdf.set_font('Arial', 'B', 12)
                name = sb.get('name', 'Unknown')
                pdf.multi_cell(self.page_width, h=6, txt=name, border=0, align='C')
                
                pdf.set_font('Arial', '', 10)
                
                # Description
                description = sb.get('description', '')
                if description:
                    pdf.set_x(left_margin)
                    pdf.multi_cell(self.page_width, h=5, txt=description, border=0, align='C')
                
                # Website
                url = sb.get('url', '')
                if url:
                    pdf.set_x(left_margin)
                    pdf.multi_cell(self.page_width, h=5, txt='Website: ' + url, border=0, align='C')
                
                # Helpline
                helpline = sb.get('helpline', '')
                if helpline:
                    pdf.set_x(left_margin)
                    pdf.multi_cell(self.page_width, h=5, txt='Helpline: ' + helpline, border=0, align='C')
                
                pdf.ln(h=3)
        
        # Format legend
        if self.formats:
            pdf.ln(h=5)
            pdf.set_font('Arial', 'B', 14)
            pdf.set_x(left_margin)
            pdf.cell(self.page_width, h=8, txt='Format Legend', border=0, ln=1, align='C')
            pdf.ln(h=5)
            
            # Sort formats by key_string for easier reading
            sorted_formats = sorted(self.formats, key=lambda f: f.get('key_string', ''))
            
            # Split into 3 columns
            num_columns = 3
            column_width = self.page_width / num_columns
            formats_per_column = (len(sorted_formats) + num_columns - 1) // num_columns  # Round up
            
            pdf.set_font('Arial', '', 8)
            start_y = pdf.get_y()
            
            # Render each column
            for col in range(num_columns):
                start_idx = col * formats_per_column
                end_idx = min(start_idx + formats_per_column, len(sorted_formats))
                current_y = start_y
                
                for fmt in sorted_formats[start_idx:end_idx]:
                    key = fmt.get('key_string', '')
                    name = fmt.get('name_string', '')
                    
                    if key and name:
                        pdf.set_xy(left_margin + (col * column_width), current_y)
                        pdf.set_font('Arial', 'B', 8)
                        pdf.cell(10, h=3.5, txt=key, border=0)
                        pdf.set_font('Arial', '', 8)
                        pdf.cell(column_width - 10, h=3.5, txt=name, border=0)
                        current_y += 3.5
            
            # Move to end of columns
            pdf.set_xy(left_margin, pdf.get_y())
            pdf.ln(h=2)


class PDFMainSectionHeader:
    def __init__(self, text, pdf_func, cell_width, line_padding=1, font='Courier', font_size=12):
        self.text = text
        self.pdf_func = pdf_func
        self.cell_width = cell_width
        self.line_padding = line_padding
        self.font = font
        self.font_size = font_size

    def copy(self):
        return PDFMainSectionHeader(
            self.text,
            self.pdf_func,
            self.cell_width,
            line_padding=self.line_padding,
            font=self.font,
            font_size=self.font_size
        )

    @property
    def height(self):
        pdf = self.pdf_func()
        pdf.set_font(self.font, 'B', self.font_size)
        return pdf.font_size + self.line_padding + 1

    def write(self, pdf, x=None, y=None):
        if x is not None and y is not None:
            pdf.set_xy(x, y)
        pdf.set_font(self.font, 'B', self.font_size)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(0, 0, 0)
        pdf.cell(self.cell_width, h=pdf.font_size + self.line_padding, txt=self.text, border=0, ln=1, align='C', fill=1)
        pdf.ln(h=1)


class PDFSubSectionHeader:
    def __init__(self, text, pdf_func, cell_width, line_padding=1, font='Courier', font_size=12):
        self.text = text
        self.pdf_func = pdf_func
        self.cell_width = cell_width
        self.line_padding = line_padding
        self.font = font
        self.font_size = font_size

    def copy(self):
        return PDFSubSectionHeader(
            self.text,
            self.pdf_func,
            self.cell_width,
            line_padding=self.line_padding,
            font=self.font,
            font_size=self.font_size
        )

    @property
    def height(self):
        pdf = self.pdf_func()
        pdf.set_font(self.font, 'B', self.font_size)
        return pdf.font_size + self.line_padding + 1

    def write(self, pdf, x=None, y=None):
        if x is not None and y is not None:
            pdf.set_xy(x, y)
        pdf.set_font(self.font, 'B', self.font_size)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(192, 192, 192)
        pdf.cell(self.cell_width, h=pdf.font_size + self.line_padding, txt=self.text, border=0, ln=1, align='C', fill=1)
        pdf.ln(h=1)


class PDFMeeting:
    QR_CODE_SIZE = 15  # mm

    def __init__(self, meeting, pdf_func, total_width, time_column_width=None, duration_column_width=None, font='Arial',
                 font_size=12, include_qr_codes=True):
        if not isinstance(meeting, Meeting):
            raise TypeError('Expected Meeting object')
        self.pdf_func = pdf_func
        self.meeting = meeting
        self.time_column_width = time_column_width if time_column_width else 15
        self.duration_column_width = duration_column_width if duration_column_width else 15
        self.font = font
        self.font_size = font_size
        self.total_width = total_width
        self.include_qr_codes = include_qr_codes
        self._qr_code_image = None

    def get_time(self):
        ampm = 'AM'
        hour, minute = str(self.meeting.start_time).split(':')[:2]
        if int(hour) > 12:
            hour = str(int(hour) - 12)
            ampm = 'PM'
        return hour + ':' + minute + ampm

    def get_duration(self):
        hour, minute = str(self.meeting.duration).split(':')[:2]
        minute = str(round(int(minute) / 60))
        return hour + '.' + minute + 'HR'

    def get_name(self):
        return self.meeting.name.strip()

    def get_location(self):
        return self.meeting.location.strip()

    def get_formats(self):
        if self.meeting.formats:
            return '(' + self.meeting.formats + ')'
        return ''

    def generate_qr_code(self):
        if not self.meeting.virtual_meeting_link or self._qr_code_image is not None:
            return self._qr_code_image

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(self.meeting.virtual_meeting_link)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        self._qr_code_image = img_bytes
        return self._qr_code_image

    def has_qr_code(self):
        """Check if meeting should display QR code (virtual or hybrid)."""
        return self.include_qr_codes and self.meeting.venue_type in [2, 3] and self.meeting.virtual_meeting_link

    def get_virtual_info(self):
        """Get formatted virtual meeting info (additional info and phone number)."""
        info_parts = []
        if self.meeting.virtual_meeting_additional_info:
            info_parts.append(self.meeting.virtual_meeting_additional_info)
        if self.meeting.phone_meeting_number:
            info_parts.append('Phone: ' + self.meeting.phone_meeting_number)
        return ' | '.join(info_parts) if info_parts else ''

    def _get_lines(self, pdf, parts, max_line_length):
        lines = []
        current_line = ''
        for i in range(len(parts)):
            part = parts[i]
            proposed_line = current_line + ' ' + part if current_line else current_line + part
            if pdf.get_string_width(proposed_line) + 2 * pdf.c_margin > max_line_length:
                lines.append(current_line)
                current_line = part
            else:
                current_line = proposed_line

            if pdf.get_string_width(current_line) + 2 * pdf.c_margin == max_line_length:
                lines.append(current_line)
                current_line = ''
            elif i == len(parts) - 1:
                lines.append(current_line)
        return lines

    @property
    def meeting_column_width(self):
        return self.total_width - self.time_column_width - self.duration_column_width

    @property
    def height(self):
        pdf = self.pdf_func()

        pdf.set_font(self.font, 'B', self.font_size)
        meeting_name = self.get_name()
        meeting_formats = self.get_formats()
        if meeting_formats:
            meeting_name += ' ' + meeting_formats
        parts = meeting_name.split()
        lines = self._get_lines(pdf, parts, self.meeting_column_width)
        text_height = pdf.font_size
        height = (text_height * len(lines))

        pdf.set_font(self.font, '', self.font_size)
        meeting_location = self.get_location()
        if meeting_location:
            parts = meeting_location.split()
            lines = self._get_lines(pdf, parts, self.meeting_column_width)
            text_height = pdf.font_size
            height += (text_height * len(lines))

        # Add height for virtual meeting info (for virtual/hybrid meetings)
        virtual_info = self.get_virtual_info()
        if virtual_info:
            parts = virtual_info.split()
            lines = self._get_lines(pdf, parts, self.meeting_column_width)
            text_height = pdf.font_size
            height += (text_height * len(lines))

        # Add space for QR code if needed (virtual or hybrid)
        if self.has_qr_code():
            height += self.QR_CODE_SIZE + 1  # QR code + 1mm spacing

        return height + pdf.line_width + 2  # 1mm line break before and after line

    def write(self, pdf, x=None, y=None):
        if x is None or y is None:
            x = pdf.get_x()
            y = pdf.get_y()
        pdf.set_xy(x, y)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(self.font, 'B', self.font_size)
        pdf.cell(self.time_column_width, h=pdf.font_size, txt=self.get_time(), ln=0, align='C')
        pdf.cell(self.duration_column_width, h=pdf.font_size, txt=self.get_duration(), ln=0, align='C')

        text = self.get_name()
        meeting_formats = self.get_formats()
        if meeting_formats:
            text += ' ' + meeting_formats
        pdf.multi_cell(self.meeting_column_width, h=pdf.font_size, txt=text, border=0, align='L')

        # Render location (for in-person and hybrid meetings)
        pdf.set_xy(x + self.duration_column_width + self.time_column_width, pdf.get_y())
        text = self.get_location()
        if text:  # Only render if there's location text
            pdf.set_font(self.font, '', self.font_size)
            pdf.multi_cell(self.meeting_column_width, h=pdf.font_size, txt=text, border=0, align='L')

        # Render virtual meeting info (additional info and phone number)
        pdf.set_xy(x + self.duration_column_width + self.time_column_width, pdf.get_y())
        virtual_info = self.get_virtual_info()
        if virtual_info:
            pdf.set_font(self.font, '', self.font_size)
            pdf.multi_cell(self.meeting_column_width, h=pdf.font_size, txt=virtual_info, border=0, align='L')

        # Render QR code (for virtual and hybrid meetings)
        if self.has_qr_code():
            qr_img = self.generate_qr_code()
            if qr_img:
                qr_x = x + self.duration_column_width + self.time_column_width
                qr_y = pdf.get_y()
                pdf.image(qr_img, x=qr_x, y=qr_y, w=self.QR_CODE_SIZE, h=self.QR_CODE_SIZE)
                pdf.set_xy(x, qr_y + self.QR_CODE_SIZE)

        pdf.ln(h=1)
        pdf.set_draw_color(211, 211, 211)
        if x is not None and y is not None:
            height = self.height - 1 - pdf.line_width
            pdf.line(x, y + height, x + self.total_width, y + height)
        else:
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + self.total_width, pdf.get_y())

        pdf.set_xy(x, pdf.get_y())
        pdf.ln(h=1)


class Booklet:
    PAPER_SIZES = {
        'letter': (216, 279),
        'legal': (216, 356),
        'tabloid': (279, 432),
    }
    VALID_FONTS = [
        'arial',
        'helvetica',
        'courier',
        'times'
    ]
    HEADER_FIELD_WEEKDAY = 'weekday'
    HEADER_FIELD_CITY = 'city'
    VALID_HEADER_FIELDS = {
        HEADER_FIELD_WEEKDAY,
        HEADER_FIELD_CITY
    }

    def __init__(self, meetings, formats, output_file, bookletize=False, paper_size='Letter', time_column_width=None,
                 duration_column_width=None, meeting_font='Arial', meeting_font_size=10, header_font='Arial',
                 header_font_size=10, main_header_field='weekday', second_header_field=None, include_qr_codes=True,
                 service_bodies=None):
        self._meetings_data = meetings
        self._formats_data = formats
        self.output_file = output_file
        self.bookletize = bookletize
        self.time_column_width = time_column_width
        self.duration_column_width = duration_column_width
        self.include_qr_codes = include_qr_codes
        self.service_bodies = service_bodies
        if paper_size.lower() not in self.PAPER_SIZES.keys():
            raise ValueError("Invalid paper size, valid choices are: {}".format(', '.join(self.PAPER_SIZES.keys())))
        self.paper_size = self.PAPER_SIZES[paper_size.lower()]
        if meeting_font.lower() not in self.VALID_FONTS:
            raise ValueError("Invalid meeting font, valid choices are: {}".format(', '.join(self.VALID_FONTS)))
        self.meeting_font = meeting_font
        self.meeting_font_size = meeting_font_size
        if header_font.lower() not in self.VALID_FONTS:
            raise ValueError("Invalid header font, valid choices are: {}".format(', '.join(self.VALID_FONTS)))
        self.header_font = header_font
        self.header_font_size = header_font_size
        if main_header_field not in self.VALID_HEADER_FIELDS:
            raise ValueError("Invalid main header field, valid choices are: {}".format(', '.join(self.VALID_HEADER_FIELDS)))
        self.main_header_field = main_header_field
        if second_header_field and second_header_field not in self.VALID_HEADER_FIELDS:
            raise ValueError("Invalid second header field, valid choices are: {}".format(', '.join(self.VALID_HEADER_FIELDS)))
        self.second_header_field = second_header_field

    def _get_pdf_obj(self):
        if self.bookletize:
            # The bookletize option is for those who don't have, don't want to use, or don't
            # know how to use the "booklet" option on their printer. It does the hard work of
            # arranging the booklet pages on paper in a landscape orientation.
            pdf = FPDF(orientation='L', format=self.paper_size)
        else:
            # This produces booklet pages as single pdf pages. They're designed to be printed
            # using the "booklet" option on a printer, meaning two per page. For this reason,
            # we're dividing the specified paper size by 2.
            pdf = FPDF(format=(self.paper_size[1] / 2, self.paper_size[0]))
        pdf.set_margins(5, 5)
        pdf.set_auto_page_break(0, 5)
        return pdf

    def get_pdf_objects(self):
        pdf = self._get_pdf_obj()
        effective_page_width = pdf.w - pdf.l_margin - pdf.r_margin
        effective_page_height = pdf.h - pdf.t_margin - pdf.b_margin
        total_width = (effective_page_width / 2) - 1 if self.bookletize else effective_page_width

        pdf.add_page()

        def _append_pdf_objects(l, objs, pos):
            height = sum([o.height for o in objs])
            if pos + height > effective_page_height:
                l.append(PDFColumnEnd())
                if not isinstance(objs[0], PDFMainSectionHeader):
                    for obj in l[::-1]:
                        if isinstance(obj, PDFMainSectionHeader):
                            cont_header = obj.copy()
                            if not cont_header.text.endswith('(Continued)'):
                                cont_header.text += ' (Continued)'
                            height += cont_header.height
                            l.append(cont_header)
                            break
                    if not isinstance(objs[0], PDFSubSectionHeader):
                        for obj in l[::-1]:
                            if isinstance(obj, PDFSubSectionHeader):
                                cont_header = obj.copy()
                                if not cont_header.text.endswith('(Continued)'):
                                    cont_header.text += ' (Continued)'
                                height += cont_header.height
                                l.append(cont_header)
                                break
                pos = 0
            l.extend(objs)
            pos += height
            return pos

        pdf_objects = []
        prev_main_header = None
        prev_second_header = None
        current_content_position = 0
        for m in self._meetings_data:
            append_objs = []
            meeting = PDFMeeting(Meeting(m), self._get_pdf_obj, total_width, time_column_width=self.time_column_width,
                                 duration_column_width=self.duration_column_width, font=self.meeting_font,
                                 font_size=self.meeting_font_size, include_qr_codes=self.include_qr_codes)
            new_main_header = getattr(meeting.meeting, self.main_header_field)
            if new_main_header != prev_main_header:
                if self.main_header_field == self.HEADER_FIELD_WEEKDAY:
                    text = weekdays[new_main_header - 1]
                else:
                    text = new_main_header
                header = PDFMainSectionHeader(
                    text,
                    self._get_pdf_obj,
                    total_width,
                    font=self.header_font,
                    font_size=self.header_font_size
                )
                append_objs.append(header)
                prev_main_header = new_main_header
                prev_second_header = None
            if self.second_header_field:
                new_second_header = getattr(meeting.meeting, self.second_header_field)
                if new_second_header != prev_second_header:
                    if self.second_header_field == self.HEADER_FIELD_WEEKDAY:
                        text = weekdays[new_second_header - 1]
                    else:
                        text = new_second_header
                    header = PDFSubSectionHeader(
                        text,
                        self._get_pdf_obj,
                        total_width,
                        font=self.header_font,
                        font_size=self.header_font_size
                    )
                    append_objs.append(header)
                    prev_second_header = new_second_header
            append_objs.append(meeting)
            current_content_position = _append_pdf_objects(pdf_objects, append_objs, current_content_position)

        return pdf_objects

    def get_pages(self):
        pdf_objects = self.get_pdf_objects()
        pages = []
        current_page = []
        for i in range(len(pdf_objects)):
            obj = pdf_objects[i]
            if isinstance(obj, PDFColumnEnd):
                pages.append(current_page)
                current_page = []
                continue
            current_page.append(obj)
            if i == len(pdf_objects) - 1:
                pages.append(current_page)
                current_page = []
        return pages

    def write_pdf(self):
        booklet_pages = self.get_pages()
        pdf = self._get_pdf_obj()
        effective_page_width = pdf.w - pdf.l_margin - pdf.r_margin
        effective_page_height = pdf.h - pdf.t_margin - pdf.b_margin

        if self.bookletize:
            # Back and front cover
            pdf.add_page()
            
            # Add cover page content if service bodies are provided
            if self.service_bodies:
                cover_page = PDFCoverPage(self.service_bodies, self._formats_data, self._get_pdf_obj, effective_page_width, effective_page_height)
                cover_page.write(pdf)

            # Write the meeting list
            column_width = (effective_page_width / 2) - 1
            total_booklet_length = len(booklet_pages)
            last_booklet_page_blank = total_booklet_length % 2 != 0
            if last_booklet_page_blank or total_booklet_length in [3, 4]:
                pdf.add_page()
                left_page = booklet_pages.pop(0)
                for obj in left_page:
                    obj.write(pdf)
            if total_booklet_length in [3, 4]:
                pdf.add_page()
                right_page = booklet_pages.pop(0)
                last_y = pdf.get_y()
                for obj in right_page:
                    obj.write(pdf, x=column_width + pdf.l_margin + 2, y=last_y)
                    last_y = pdf.get_y()

            while booklet_pages:
                pdf.add_page()
                even_pdf_page = pdf.page_no() % 2 == 1
                original_y = pdf.get_y()

                left_page = booklet_pages.pop() if even_pdf_page else booklet_pages.pop(0)
                for obj in left_page:
                    obj.write(pdf)

                if booklet_pages:
                    last_y = original_y
                    right_page = booklet_pages.pop(0) if even_pdf_page else booklet_pages.pop()
                    for obj in right_page:
                        obj.write(pdf, x=column_width + pdf.l_margin + 2, y=last_y)
                        last_y = pdf.get_y()
        else:
            # Add cover page for non-bookletize mode
            if self.service_bodies:
                pdf.add_page()
                cover_page = PDFCoverPage(self.service_bodies, self._formats_data, self._get_pdf_obj, effective_page_width, effective_page_height)
                cover_page.write(pdf)
            
            for page in booklet_pages:
                pdf.add_page()
                for obj in page:
                    obj.write(pdf)

        pdf.output(self.output_file)
        return
