import re
import telebot
import zeep
import auth_data
import my_dialogflow as df
import time


def replace_p(string: str, start: int, end: int, old: str, new: str):
    """
    Функция заменяет символы old  на симводы new в строке string
    начиная с символа с индексом start и заканечива символом с индексом (end - 1)
    :param string:
    :param start:
    :param end:
    :param old:
    :param new:
    :return:
    """
    return string[:start] + string[start:end].replace(old, new) + string[end:]


def get_check_digit(num: int) -> int:
    """
    Проверка контрольной цифры в соответствии с форматоом S10
    :param num:
    :return:
    """
    weights = [8, 6, 4, 2, 3, 5, 9, 7]
    control_sum = 0
    for i, digit in enumerate(f"{num:08}"):
        control_sum += weights[i] * int(digit)
    control_sum = 11 - (control_sum % 11)
    if control_sum == 10:
        control_sum = 0
    elif control_sum == 11:
        control_sum = 5
    return control_sum


def chek_barcode(message_text: str):
    """
    Функция проверки трек-номера на корректность
    :param message_text: Строка содержащая один или несколько идентификаторов почтового отправления
            - международный, состоящий из 13 символов (буквенно-цифровой) в формате S10
            - внутрироссийский, состоящий из 14 символов (цифровой)
    :return:
    """

    barcodes = re.findall("(?:[A-Z]{2}(?:\d|O|О){9}[A-Z]{2})|(?:(?:\d|O|О){14})", message_text)
    barcodes_dic = {}
    if barcodes:
        for i in range(len(barcodes)):
            if len(barcodes[i]) == 14:
                barcodes[i] = re.sub("O|О", "0", barcodes[i])
                barcodes_dic[barcodes[i]] = True
            elif len(barcodes[i]) == 13:
                barcodes[i] = barcodes[i][0:3] + re.sub("O|О", "0", barcodes[i][3:10]) + barcodes[i][10:]
                # Проверка 10-го символа - контрольной цифры по формату S10
                barcodes_dic[barcodes[i]] = (int(barcodes[i][10]) == get_check_digit(int(barcodes[i][2:10])))
    return barcodes_dic


def send_message_formatting(location):
    # f"{location.ItemParameters.Barcode.strip()}\n" \
    return f"{location.AddressParameters.OperationAddress.Index.strip()} " \
                             f"{location.AddressParameters.OperationAddress.Description.strip()}\n" \
                             f"{location.OperationParameters.OperDate.strftime('%d.%m.%Y %H:%M:%S %Z')}\n" \
                             f"{location.OperationParameters.OperType.Name} " \
                             f"({location.OperationParameters.OperAttr.Name})"


def get_last_location_russian_post(login: str, password: str, message_text: str):
    """
    Функция возвращает сообщение с данным о почтовом отправлении, псследнее его местонахождение
    :param login: логин в системе API почты Росиии
    :param password: пароль в системе API почты России
    :param message_text:  Трек-номер почтового отправления
    :return:
    """

    '''
    # Заменим случайные буквы O на нули
        if len(message_text) == 14:
            message_text = re.sub("O", "0", barcode)
        elif len(message_text) == 13:
            barcode = message_text[0:3] + re.sub("O", "0", message_text[3:10]) + message_text[10:]
    '''

    # Извлечем из сообщения трек-номера
    barcodes_dic = chek_barcode(message_text)
    if len(barcodes_dic) == 0:
        return ["Не совсем понимаю, о чём Вы. Трек-номер в Вашем сообщении не не найден.",
                "Международный почтовый трек выглядит так: AB123456789CD \nВнутрироссийский — так: 12345678901234"]

    # Схема WSDL на сайте Почты России. В ней нет указания на необязательность некоторых елементов в ответном сообщеии.
    # wsdl = 'https://tracking.russianpost.ru/tracking-web-static/rtm34_wsdl.xml'
    # Временно используется локальная схема
    wsdl = 'russisnpost\\rtm34_wsdl.xml'

    # Создаём объект по схеме WSDL
    client = zeep.Client(wsdl=wsdl)

    send_messages = []
    for barcode, is_true in barcodes_dic.items():
        if is_true:
            try:
                result = client.service.getOperationHistory({'Barcode': barcode, 'MessageType': 0, 'Language': 'RUS'},
                                                            {'login': login, 'password': password})
                if result:
                    last_location = result[len(result) - 1]
                    send_message = send_message_formatting(last_location)
                else:
                    send_message = f"Отправление с трек-номером {barcode} не найдено."
            except Exception as ex:
                print(ex)
                print("Что-то пошло нет так. Проверьте правильность трек-номера")
                send_message = f"{ex}\nЧто-то пошло нет так. Проверьте правильность трек-номера."
        else:
            send_message = "Трек-номер не корректный"
        send_messages.append(f"Трек-номер: {barcode}\n {send_message}\n")
    # print(send_messages)
    return send_messages


def telegram_bot(token):
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start"])
    def start_message(message):
        bot.send_message(message.chat.id, "Здравствуйте. Я бот, меня зовут Аля.\n"
                         "Я умею находить текущее местоположение почтового отправления по его трек-номеру.\n"
                         "Просто сообщите мне нужный номер или несколько и я найду, где они сейчас.")

    @bot.message_handler(content_types=["text"])
    def send_text(message):
        to_do = df.dialogflow_get_todo(auth_data.dialogflow_settings, message.chat.id, message.text)
        if re.findall("(?:[A-Z]{2}(?:\d|O|О){9}[A-Z]{2})|(?:(?:\d|O|О){14})", message.text.strip().upper()):

            send_messages_text = get_last_location_russian_post(auth_data.russian_post_login,
                                                                auth_data.russian_pos_password,
                                                                message.text.strip().upper())
            for text in send_messages_text:
                bot.send_message(message.chat.id, text)
        elif re.findall("([\d]{4,})",message.text.strip().upper()):
            bot.send_message(message.chat.id, "DosntLoolLilkBarcode")
        else:
            to_telegram_text = df.dialogflow_get(auth_data.dialogflow_settings,
                                                                message.chat.id, message.text)

            bot.send_message(message.chat.id, to_telegram_text if to_telegram_text != '' else 'Кажется Аля не знает,'
                                                                                              'что ответить. Извините.')

    bot.polling()



def main():
    df.dialogflow_init(auth_data.dialogflow_key_json)
    telegram_bot(auth_data.token_bot)


if __name__ == '__main__':
   main()

