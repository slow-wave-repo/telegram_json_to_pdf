#!/usr/bin/env python3


import glob
import json
import locale
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import emoji
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


class JsonPdf:
    TEXT = 'text'
    TITLE = 'title_style'
    PERIOD = 'period_style'
    DATE = 'date_style'
    NAME = 'name_style'
    SELF_MESSAGE = 'self_message_style'
    PARTNER_MESSAGE = 'partner_message_style'

    REGULAR = "regular.ttf"
    BOLD = "bold.ttf"

    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

    pdfmetrics.registerFont(TTFont('Font', REGULAR))
    pdfmetrics.registerFont(TTFont('FontBold', BOLD))

    text_style = ParagraphStyle(name='TextStyle',
                                fontName='Font',
                                fontSize=12)
    title_style = ParagraphStyle(name='TitleStyle',
                                 fontName='FontBold',
                                 fontSize=40,
                                 alignment=TA_CENTER,
                                 bold=True,
                                 textTransform='uppercase')
    period_style = ParagraphStyle(name='PeriodStyle',
                                  fontName='Font',
                                  fontSize=10,
                                  alignment=TA_CENTER)
    date_style = ParagraphStyle(name='DateStyle',
                                fontName='Font',
                                fontSize=8,
                                alignment=TA_CENTER,
                                textColor='grey')
    name_style = ParagraphStyle(name='NameStyle',
                                fontName='Font',
                                fontSize=12,
                                alignment=TA_CENTER,
                                textTransform='uppercase')
    self_message_style = ParagraphStyle(name='SelfMessageStyle',
                                        fontName='Font',
                                        bold=True,
                                        fontSize=11,
                                        alignment=TA_RIGHT,
                                        leading=15)
    partner_message_style = ParagraphStyle(name='PartnerMessageStyle',
                                           fontName='Font',
                                           fontSize=11,
                                           textColor='grey')

    media_types = {
        'voice_message': '(VOICE MESSAGE)',
        'video_message': '(VIDEO MESSAGE)',
        'video': '(VIDEO)',
        'photo': '(PHOTO)',
        'sticker': '(STICKER)',
        'other': '(OTHER)',
        'call': '(CALL)'
    }

    def style(self, message: str, type: str) -> Paragraph:
        if type == 'text':
            return Paragraph(message, self.text_style)
        elif type == 'title':
            return Paragraph(message, self.title_style)
        elif type == 'period':
            return Paragraph(message, self.period_style)
        elif type == 'name':
            return Paragraph(message, self.name_style)
        if type == 'self_message':
            return Paragraph(message, self.self_message_style)
        elif type == 'partner_message':
            return Paragraph(message, self.partner_message_style)
        elif type == 'date_style':
            return Paragraph(message, self.date_style)
        else:
            return self.style(message, 'text')

    def format_date_inside(self, date_str: str) -> str:
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime('%e %B %Y')

        return formatted_date

    def format_date_name(self, date_str: str) -> str:
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime("%d.%m.%Y")

        return formatted_date

    def get_time_borders(self, input_data):
        earliest_date = None
        latest_date = None

        for message in input_data['messages']:
            current_date = message['date']

            if earliest_date is None or current_date < earliest_date:
                earliest_date = current_date

            if latest_date is None or current_date > latest_date:
                latest_date = current_date

        return earliest_date, latest_date

    def check_message(self, message: str) -> str:
        result = message.replace('\n', '<br/><br/>')

        return emoji.replace_emoji(result, '(EMOJI)')

    def check_if_json(self, file_path: str) -> bool:
        file = Path(file_path)
        return file.suffix == '.json'

    def check_if_pdf_exists(self, path):
        return not os.path.exists(path)


class PersonalChatJsonPdf(JsonPdf):
    def __init__(self, input_file: str):
        with open(input_file, 'r', encoding='utf-8') as opened_file:
            self.data = json.load(opened_file)

        self.input_file = input_file
        self.name = self.data['name']
        self.earliest_date, self.latest_date = self.get_time_borders(self.data)
        self.time_period_inside = f'{self.format_date_inside(self.earliest_date)} — {self.format_date_inside(self.latest_date)}'
        self.time_period_name = f'{self.format_date_name(self.earliest_date)} — {self.format_date_name(self.latest_date)}'

    def choose_role_tag(self, message, name: str, story: list):
        if name == self.data['name']:
            story.append(self.style(message, 'partner_message'))
        else:
            story.append(self.style(message, 'self_message'))

    def make_pdf(self):
        if self.check_if_pdf_exists(f'/home/{os.getlogin()}/Desktop/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'):
            previous_date = None

            path = Path(f'/home/{os.getlogin()}/Desktop/JSONtoPDF/{self.name}/')
            path.mkdir(parents=True, exist_ok=True)

            pdf_output_path = f'/home/{os.getlogin()}/Desktop/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'
            doc = SimpleDocTemplate(pdf_output_path, pagesize=A4)
            story = []

            story.append(self.style(f"{self.data['name']}", 'title'))
            story.append(Spacer(1, 40))
            story.append(self.style(f"{self.time_period_inside}", 'period'))

            for message in self.data['messages']:
                if self.format_date_inside(message['date']) != previous_date:
                    story.append(Spacer(1, 48))

                    story.append(
                        HRFlowable(width="50%", thickness=1, lineCap='round', spaceBefore=0.3 * cm,
                                   spaceAfter=0.5 * cm, hAlign='CENTER'))

                    story.append(self.style(f"— {self.format_date_inside(message['date'])} —", 'date_style'))

                    story.append(
                        HRFlowable(width="50%", thickness=1, lineCap='round', spaceBefore=0.3 * cm,
                                   spaceAfter=0.5 * cm, hAlign='CENTER'))

                    story.append(Spacer(1, 30))

                    previous_date = self.format_date_inside(message['date'])

                if message['type'] == 'service':
                    self.choose_role_tag(self.media_types['call'], message['actor'], story)
                elif isinstance(message['text'], list):
                    self.choose_role_tag(self.media_types['call'], message['from'], story)
                else:
                    self.choose_role_tag(self.check_message(message['text']), message['from'], story)
                    story.append(Spacer(1, 20))
                if 'media_type' in message:
                    try:
                        self.choose_role_tag(self.media_types[message['media_type']], message['from'], story)
                    except KeyError:
                        self.choose_role_tag(self.media_types['other'], message['from'], story)

            doc.build(story)

            new_name = f'/home/{os.getlogin()}/Desktop/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'

            os.rename(pdf_output_path, new_name)
            shutil.move(self.input_file, f'/home/{os.getlogin()}/Desktop/JSONtoPDF/{self.name}/{os.path.basename(self.input_file)}')
            os.system(f'xdg-open "{new_name}"')

            os.system('clear')
            print(f"{self.name}, {self.time_period_name}.pdf is ready!")
        else:
            os.system('clear')
            print('\nThis PDF-file already exists!')

        input('\nPress any key to close...')
        os.system('clear')


class ChooseJson:
    def __init__(self, path=f'/home/{os.getlogin()}/'):
        self.directory_path = path

        if os.path.isdir(self.directory_path):
            self.menu = {}

            self.json_files = glob.glob(os.path.join(self.directory_path, '**/*.json'), recursive=True)
            counter = 0

            for json_file in self.json_files:
                counter += 1

                self.menu[counter] = json_file

            self.fill_terminal_width()
            print('Telegram-JSON to PDF Converter')
            self.fill_terminal_width()
            print()

            for item in self.menu:
                print(f'{item} -- {self.menu[item]} \n')

            self.fill_terminal_width()
            print('\n0 -- Exit')

            process_file = self.choose()
        else:
            process_file = PersonalChatJsonPdf(self.directory_path)

        process_file.make_pdf()

    def fill_terminal_width(self):
        print('-' * shutil.get_terminal_size()[0])

    def choose(self):
        print()
        self.fill_terminal_width()

        try:
            option = int(input('\nChoose: '))
        except ValueError:
            return self.choose()

        if option == 0:
            os.system('clear')
            quit()
        elif option not in list(self.menu):
            return self.choose()
        else:
            return PersonalChatJsonPdf(self.menu[int(option)])


if __name__ == '__main__':
    os.system('clear')
    argument = sys.argv

    if len(argument) > 1:
        ChooseJson(argument[1])
    else:
        ChooseJson()
