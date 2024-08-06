#!/usr/bin/env python3


import argparse
import glob
import json
import locale
import os
import shutil
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

    REGULAR = 'fonts/regular.ttf'
    BOLD = 'fonts/bold.ttf'

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
                                  fontSize=12,
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
                                        leading=15,
                                        spaceBefore=25,
                                        spaceAfter=25)
    partner_message_style = ParagraphStyle(name='PartnerMessageStyle',
                                           fontName='Font',
                                           fontSize=11,
                                           textColor='grey',
                                           leading=15,
                                           spaceBefore=25,
                                           spaceAfter=25
                                           )
    actor_style = ParagraphStyle(name='ActorStyle',
                                 fontName='Font',
                                 fontSize=13,
                                 alignment=TA_CENTER,
                                 textColor='grey',
                                 spaceBefore=25,
                                 spaceAfter=25
                                 )

    actor_message_style = ParagraphStyle(name='ActorMessageStyle',
                                         fontName='Font',
                                         alignment=TA_CENTER,
                                         fontSize=12,
                                         leading=15,
                                         spaceBefore=25,
                                         spaceAfter=25
                                         )

    media_types = {
        'voice_message': '(VOICE MESSAGE)',
        'video_message': '(VIDEO MESSAGE)',
        'video': '(VIDEO)',
        'photo': '(PHOTO)',
        'sticker': '(STICKER)',
        'other': '(OTHER)',
        'call': '(CALL)'
    }

    def __init__(self, input_file, directory_path, path_save=f'/home/{os.getlogin()}/Desktop'):

        self.directory_path = directory_path
        self.input_file = input_file
        self.path_save = path_save

        self.name = self.input_file['name']
        self.earliest_date, self.latest_date = self.get_time_borders(self.input_file)
        self.time_period_inside = f'{self.format_date_inside(self.earliest_date)} — {self.format_date_inside(self.latest_date)}'
        self.time_period_name = f'{self.format_date_name(self.earliest_date)} — {self.format_date_name(self.latest_date)}'

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
        elif type == 'actor_style':
            return Paragraph(message, self.actor_style)
        elif type == 'actor_message_style':
            return Paragraph(message, self.actor_message_style)
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

    def choose_role_tag(self, message, name: str, story: list):
        if name == self.input_file['name']:
            story.append(self.style(message, 'partner_message'))
        else:
            story.append(self.style(message, 'self_message'))

    def make_pdf(self):
        if self.check_if_pdf_exists(f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'):
            previous_date = None

            path = Path(f'{self.path_save}/JSONtoPDF/{self.name}/')
            path.mkdir(parents=True, exist_ok=True)

            pdf_output_path = f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'
            doc = SimpleDocTemplate(pdf_output_path, pagesize=A4)
            story = []

            story.append(self.style(f"{self.input_file['name']}", 'title'))
            story.append(Spacer(1, 40))
            story.append(self.style(f"{self.time_period_inside}", 'period'))

            for message in self.input_file['messages']:
                if self.format_date_inside(message['date']) != previous_date:
                    story.append(Spacer(1, 30))

                    story.append(
                        HRFlowable(width="50%", thickness=1, lineCap='round', spaceBefore=0.3 * cm,
                                   spaceAfter=0.5 * cm, hAlign='CENTER'))

                    story.append(self.style(f"— {self.format_date_inside(message['date'])} —", 'date_style'))

                    story.append(
                        HRFlowable(width="50%", thickness=1, lineCap='round', spaceBefore=0.3 * cm,
                                   spaceAfter=0.5 * cm, hAlign='CENTER'))

                    previous_date = self.format_date_inside(message['date'])

                if message['type'] == 'service' and message['action'] == 'phone_call':
                    self.choose_role_tag(self.media_types['call'], message['actor'], story)

                if isinstance(message['text'], list):
                    message_result = ''

                    for part in message['text']:
                        if isinstance(part, dict) and part['type'] == 'mention':
                            message_result += f'<a href="https://t.me/{part["text"][1:].lower()}" color=grey underline=True>{part["text"]}</a>'

                        elif isinstance(part, dict) and part['type'] == 'link':
                            message_result += f'<a href="{part["text"]}" color=grey underline=True>{part["text"]}</a>'

                        elif isinstance(part, dict) and part['type'] == 'text_link':
                            message_result += f'<a href="{part["href"]}" color=grey underline=True>{part["text"]}</a>'

                        elif isinstance(part, dict):
                            pass

                        else:
                            message_result += part

                    try:
                        self.choose_role_tag(self.check_message(message_result), message['from'], story)
                    except KeyError:
                        self.choose_role_tag(self.check_message(message_result), message['actor'], story)

                else:
                    try:
                        self.choose_role_tag(self.check_message(message['text']), message['from'], story)
                    except KeyError:
                        self.choose_role_tag(self.check_message(message['text']), message['actor'], story)

            doc.build(story)

            new_name = f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'

            os.rename(pdf_output_path, new_name)
            shutil.copy(self.directory_path,
                        f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.json')
            os.system(f'xdg-open "{new_name}"')

            os.system('clear')
            print(f"{self.name}, {self.time_period_name}.pdf is ready!")

            if self.path_save == f'/home/{os.getlogin()}/Desktop':
                print(f'\nCopied to Desktop.')
            elif self.path_save == f'.':
                print(f'\nCopied to {os.getcwd()}')
            else:
                print(f'\nCopied to {self.path_save}')
        else:
            os.system('clear')
            print('\nThis PDF-file already exists!')

        input('\nPress any key to close...')
        os.system('clear')


class PrivateGroupJsonPdf(JsonPdf):

    def make_pdf(self):
        if self.check_if_pdf_exists(f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'):
            previous_date = None
            previous_actor = None

            path = Path(f'{self.path_save}/JSONtoPDF/{self.name}/')
            path.mkdir(parents=True, exist_ok=True)

            pdf_output_path = f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'
            doc = SimpleDocTemplate(pdf_output_path, pagesize=A4)
            story = []

            story.append(story.append(self.style(f"{self.input_file['name']}", 'title')))
            story.append(Spacer(1, 40))
            story.append(self.style(f"{self.time_period_inside}", 'period'))

            for message in self.input_file['messages']:
                # Date of message
                if self.format_date_inside(message['date']) != previous_date:
                    story.append(Spacer(1, 30))

                    story.append(
                        HRFlowable(width="50%", thickness=1, lineCap='round', spaceBefore=0.3 * cm,
                                   spaceAfter=0.5 * cm, hAlign='CENTER'))

                    story.append(self.style(f"— {self.format_date_inside(message['date'])} —", 'date_style'))

                    story.append(
                        HRFlowable(width="50%", thickness=1, lineCap='round', spaceBefore=0.3 * cm,
                                   spaceAfter=0.5 * cm, hAlign='CENTER'))

                    previous_date = self.format_date_inside(message['date'])

                # If service message
                if message['type'] == 'service' and (
                        message['action'] == 'invite_members' or message['action'] == 'create_group'):
                    invites_members = message['members']
                    edited_invites_members = ','.upper().join(invites_members)
                    story.append(
                        self.style(self.check_message(f'{message["actor"].upper()} invited {edited_invites_members}'),
                                   'actor_style'))

                elif message['type'] == 'service' and message['action'] == 'join_group_by_link':
                    story.append(self.style(f'{message["actor"].upper()} joined', 'actor_style'))

                elif 'actor' in list(message.keys()):
                    if message['actor'] != previous_actor:
                        story.append(self.style(self.check_message(message["actor"].upper()), 'actor_style'))
                        previous_actor = message['actor']

                else:
                    if message['from'] != previous_actor:
                        story.append(self.style(self.check_message(message["from"].upper()), 'actor_style'))
                        previous_actor = message['from']

                # Message body
                if message['type'] == 'message':

                    if 'photo' in list(message):
                        story.append(
                            self.style(self.check_message(f'(PHOTO) {message["text"]}'), 'actor_message_style'))

                    elif 'video' in list(message):
                        story.append(
                            self.style(self.check_message(f'(VIDEO) {message["text"]}'), 'actor_message_style'))

                    elif 'audio' in list(message):
                        story.append(
                            self.style(self.check_message(f'(AUDIO) {message["text"]}'), 'actor_message_style'))

                    if isinstance(message['text'], list):
                        message_result = ''

                        for part in message['text']:
                            if isinstance(part, dict) and part['type'] == 'mention':
                                message_result += f'<a href="https://t.me/{part["text"][1:].lower()}" color=grey underline=True>{part["text"]}</a>'

                            elif isinstance(part, dict) and part['type'] == 'link':
                                message_result += f'<a href="{part["text"]}" color=grey underline=True>{part["text"]}</a>'

                            elif isinstance(part, dict) and part['type'] == 'text_link':
                                message_result += f'<a href="{part["href"]}" color=grey underline=True>{part["text"]}</a>'

                            elif isinstance(part, dict):
                                pass

                            else:
                                message_result += part

                        story.append(self.style(self.check_message(message_result), 'actor_message_style'))


                    else:
                        story.append(self.style(self.check_message(message['text']), 'actor_message_style'))

            doc.build(story)

            new_name = f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.pdf'

            os.rename(pdf_output_path, new_name)
            shutil.copy(self.directory_path,
                        f'{self.path_save}/JSONtoPDF/{self.name}/{self.name}, {self.time_period_name}.json')
            os.system(f'xdg-open "{new_name}"')

            # os.system('clear')
            print(f"{self.name}, {self.time_period_name}.pdf is ready!")

            if self.path_save == f'/home/{os.getlogin()}/Desktop':
                print(f'\nCopied to Desktop.')
            elif self.path_save == f'.':
                print(f'\nCopied to {os.getcwd()}')
            else:
                print(f'\nCopied to {self.path_save}')
        else:
            os.system('clear')
            print('\nThis PDF-file already exists!')

        input('\nPress any key to close...')
        os.system('clear')


class ChooseJson:
    def __init__(self, path=f'/home/{os.getlogin()}/', path_save=f'/home/{os.getlogin()}/Desktop'):
        self.directory_path = path
        self.path_save = path_save

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
            self.choose()
        else:
            with open(self.directory_path, 'r', encoding='utf-8') as opened_file:
                self.data = json.load(opened_file)
                self.determine_type_of_chat(self.directory_path)

    def fill_terminal_width(self):
        print('-' * shutil.get_terminal_size()[0])

    def determine_type_of_chat(self, path):
        if self.data['type'] == 'personal_chat':
            PersonalChatJsonPdf(self.data, path, self.path_save).make_pdf()
        elif self.data['type'] == 'private_group':
            PrivateGroupJsonPdf(self.data, path, self.path_save).make_pdf()
        else:
            pass

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
            self.choose()
        else:
            with open(self.menu[int(option)], 'r', encoding='utf-8') as opened_file:
                self.data = json.load(opened_file)
                self.determine_type_of_chat(self.menu[int(option)])


if __name__ == '__main__':
    os.system('clear')
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('-d', '--destination', type=str, )
    args = parser.parse_args()

    if args.file and args.destination:
        ChooseJson(path=f'{args.file}', path_save=f'{args.destination}')
    elif args.file and not args.destination:
        ChooseJson(path=f'{args.file}')
    elif args.destination and not args.file:
        ChooseJson(path_save=f'{args.destination}')
    else:
        ChooseJson()
