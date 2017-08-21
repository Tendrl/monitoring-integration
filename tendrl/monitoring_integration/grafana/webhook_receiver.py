import sys


from gevent import socket


from tendrl.commons.utils import log_utils as logger
 
HOST = '127.0.0.1'
PORT = 999


def server():
    try:
        request = client_connection.recv(1024)

        http_response = """\
            HTTP/1.1 200 OK
            """
        client_connection.sendall(http_response)

    except Exception, ex:
        logger.log("info", NS.get("publisher_id", None),
                       {'message': str(ex)})
        raise ex
    finally:
        sys.stdout.flush()
        s.close()


def start_server():

    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind((HOST, PORT))
    except socket.error as msg:
        msg =  'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        logger.log("info", NS.get("publisher_id", None),
                       {'message': msg})
        sys.exit()

    logger.log("info", NS.get("publisher_id", None),
                       {'message': "Socket Bind Complete"})

    #Start listening on socket
    listen_socket.listen(1)

    while True:
        client_connection, client_address = listen_socket.accept()
        server()
