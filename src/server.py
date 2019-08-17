#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory, connectionDone
from time import gmtime, strftime


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""

    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI

    # указание фабрики для обработки подключений
    factory: 'Server'

    # информация о клиенте
    ip: str
    login: str = None

    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """

        self.ip = self.transport.getPeer().host  # записываем IP адрес клиента
        self.factory.clients.append(self)  # добавляем в список клиентов фабрики
#        for i in self.factory.clients:
#            print(i, end="")

#        self.sendLine("Welcome to the chat!".encode())  # отправляем сообщение клиенту

        print(f"Client {self.ip} connected")  # отображаем сообщение в консоли сервера

    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """

        self.factory.clients.remove(self)  # удаляем клиента из списка в фабрике

        print(f"Client {self.ip} disconnected")  # выводим уведомление в консоли сервера

    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента

        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован
        """

        message = line.decode()  # раскодируем полученное сообщение в строку
        newlogin = message.replace("login:", "")

#        print(f"USERS0: COUNT: {len(self.factory.clients)}")
#        print(f"LOGIN0: {self.login}")
        # если логин еще не зарегистрирован
        if self.login is None:
            if message.startswith("login:"):  # проверяем, чтобы в начале шел login:

                user_count = 0
                user_exists = False

                for user in self.factory.clients:    #check dublicates
#                    print(f"USER NUMBER: {user_count}")
#                    print(f"USER1 COUNT: {len(self.factory.clients)}")
#                    print(f"OLD LOGIN: {user.login}")  #old users
#                    print(f"NEW LOGIN: {self.login}")  #new user
#                    print(f"NEWLOGIN: {newlogin}")
                    if newlogin == user.login:
                        user_exists = True
                        break
                    user_count += 1

                if user_exists:
                    print(f"NEW USER EXISTS: {self.login}. REMOVE!")
                    self.sendLine("Login exists, try again".encode())
                    self.transport.loseConnection(self)
                else:
                    self.login = newlogin
                    # формируем уведомление о новом клиенте
                    notification = f"New user: {self.login}"
                    # отсылаем всем в чат
                    self.factory.notify_about_new_users(notification)
                    self.sendLine("Welcome to the chat!".encode())  # отправляем сообщение клиенту

                    #send 10 messages to new client
                    if self.factory.chat:
                        self.sendLine("Last 10 messages:".encode())
                        for message in self.factory.chat[-10:]:
                            self.sendLine(message)
#                            print(message)
            else:
                # шлем уведомление, если в сообщении ошибка
                self.sendLine("Invalid login".encode())
        # если логин уже есть и это следующее сообщение
        else:
            # форматируем сообщение от имени клиента
            format_message = f"{self.login}: {message}"

            # отсылаем всем в чат и в консоль сервера
            self.factory.notify_all_users(format_message)
            print(format_message)


class Server(ServerFactory):
    """Класс для управления сервером"""

    clients: list  # список клиентов
    protocol = Client  # протокол обработки клиента
    chat: list = []   #chat list

    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """

        self.clients = []  # создаем пустой список клиентов


        print("Server started - OK")  # уведомление в консоль сервера

    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""

        print("Start listening ...")  # уведомление в консоль сервера

    def notify_about_new_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        about new user
        """

        data = message.encode()  # закодируем текст в двоичное представление

        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)

    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """

        message_with_time = strftime("%X", gmtime()) + "  " + message
        # закодируем текст в двоичное представление
        data = message_with_time.encode()
        self.chat.append(data)

        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )

    # запускаем реактор
    reactor.run()
