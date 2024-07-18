#!/usr/bin/env python3


import json
import locale
import os
import glob
from pathlib import Path
from datetime import datetime

from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


class Settings:
    TEXT = 'text'
    TITLE = 'title_style'
    PERIOD = 'period_style'
    DATE = 'date_style'
    NAME = 'name_style'
    SELF_MESSAGE = 'self_message_style'
    PARTNER_MESSAGE = 'partner_message_style'

    font_regular_path = "regular.ttf"
    font_bold_path = "bold.ttf"

    pdfmetrics.registerFont(TTFont('Font', font_regular_path))
    pdfmetrics.registerFont(TTFont('FontBold', font_bold_path))

    text_style = ParagraphStyle(name='TextStyle', fontName='Font', fontSize=14)
    title_style = ParagraphStyle(name='TitleStyle', fontName='FontBold', fontSize=40, alignment=TA_CENTER, bold=True,
                                 textTransform='uppercase')
    period_style = ParagraphStyle(name='PeriodStyle', fontName='Font', fontSize=16, alignment=TA_CENTER)
    date_style = ParagraphStyle(name='DateStyle', fontName='Font', fontSize=14, alignment=TA_RIGHT)
    name_style = ParagraphStyle(name='NameStyle', fontName='Font', fontSize=14, alignment=TA_CENTER,
                                textTransform='uppercase')
    self_message_style = ParagraphStyle(name='SelfMessageStyle', fontName='FontBold', bold=True, fontSize=14, alignment=TA_RIGHT)
    partner_message_style = ParagraphStyle(name='PartnerMessageStyle', fontName='Font', fontSize=14)

    def style(self, message: str, type) -> Paragraph:
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



class PersonalChat(Settings):
    def __init__(self, file):
        with open(file, 'r', encoding='utf-8') as opened_file:
            self.data = json.load(opened_file)

        self.name = self.data['name']
        self.earliest_date, self.latest_date = self.get_time_borders(self.data)
        self.time_period_inside = f'{self.format_date_inside(self.earliest_date)} — {self.format_date_inside(self.latest_date)}'
        self.time_period_name = f'{self.format_date_name(self.earliest_date)} — {self.format_date_name(self.latest_date)}'

    def choose_role_tag(self, message, name, story):
        if name == self.data['name']:
            story.append(self.style(message, 'partner_message'))
        else:
            story.append(self.style(message, 'self_message'))

    def format_date_inside(self, date_str):
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime('%d %B %Y')

        return formatted_date

    def format_date_name(self, date_str):
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime("%d.%m.%Y")

        return formatted_date

    def check_if_json(self, file_path):
        file = Path(file_path)
        return file.suffix == '.json'

    def get_time_borders(self, data):
        earliest_date = None
        latest_date = None

        for message in data['messages']:
            current_date = message['date']

            if earliest_date is None or current_date < earliest_date:
                earliest_date = current_date

            if latest_date is None or current_date > latest_date:
                latest_date = current_date

        return earliest_date, latest_date


    def make_pdf(self):
        previous_date = None

        story = []

        story.append(self.style(f"{self.data['name']}", 'title'))
        story.append(Spacer(1, 40))
        story.append(self.style(f"{self.time_period_inside}", 'period'))
        story.append(Spacer(1, 16))

        media_types = {
            'voice_message': '— VOICE MESSAGE —',
            'video_message': '— VIDEO MESSAGE —',
            'video': '— VIDEO —',
            'photo': '— PHOTO —',
            'sticker': '— STICKER —',
            'other': '— OTHER —',
            'call': '— CALL —'
        }

        for message in self.data['messages']:
            if self.format_date_inside(message['date']) != previous_date:
                story.append(Spacer(1, 48))

                story.append(self.style(f"{self.format_date_inside(message['date'])}", 'date_style'))

                story.append(Spacer(1, 36))

                previous_date = self.format_date_inside(message['date'])

            if message['type'] == 'service':
                self.choose_role_tag(media_types['call'], message['actor'], story)
            elif isinstance(message['text'], list):
                self.choose_role_tag(media_types['call'], message['from'], story)
            else:
                self.choose_role_tag(message['text'], message['from'], story)
                story.append(Spacer(1, 12))
                story.append(Spacer(1, 12))
            if 'media_type' in message:
                try:
                    self.choose_role_tag(media_types[message['media_type']], message['from'], story)
                except KeyError:
                    self.choose_role_tag(media_types['other'], message['from'], story)

        doc.build(story)

        new_name = f"{self.name}, {self.time_period_name}"

        os.rename(pdf_output_path, new_name)


locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

directory_path = '/home/xxvnt4/Desktop'
pdf_output_path = "result.pdf"
doc = SimpleDocTemplate(pdf_output_path, pagesize=A4)

json_files = glob.glob(os.path.join(directory_path, '**/*.json'), recursive=True)

print('List of Telegram-JSONs:\n')
counter = 0

for json_file in json_files:
    counter += 1

    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

        if 'type' in data.keys() and 'id' in data.keys() and 'messages' in data.keys():
            print(f'({counter}) {json_file} \n')

process_file = PersonalChat('result.json')
process_file.make_pdf()



print(f"{data['name']} is ready!")
