#!/usr/bin/env python3
import socket
import os
import sys
import signal
import re
import hashlib

def metoda_citanie(slovnik):
    reply_c = ""
    header_c = ""
    status_code = 100
    status_msg = "OK"


    try:
        with open(f'{slovnik["Mailbox"]}/{slovnik["Message"]}') as message_file:
            reply_c = message_file.read()
            length = len(reply_c)
            header_c = (f'Content-length {length}\n')

    except FileNotFoundError:
        status_code, status_msg = (201, 'No such message')
    except OSError:
        status_code, status_msg = (202, 'Read error')
    except KeyError:
        status_code, status_msg = (200, 'Bad request')

    return (header_c, reply_c, status_code, status_msg)


def metoda_ls(slovnik):
    reply_c = ""
    header_c = ""
    status_code = 100
    status_msg = "OK"

    try:
        zoznam_sp = os.listdir(slovnik["Mailbox"])
        zoznam_len = len(zoznam_sp)

        header_c = (f'Number-of-messages: {zoznam_len}\n')
        reply_c = "\n".join(zoznam_sp) + "\n"

    except FileNotFoundError:
        status_code, status_msg = (203, 'No such mailbox')
    except KeyError:
        status_code, status_msg = (200, 'Bad request')

    return (header_c, reply_c, status_code, status_msg)


def metoda_pisanie(slovnik, input_file):
    reply_c = ""
    header_c = ""
    status_code = 100
    status_msg = "OK"

    try:
        sprava_obs = input_file.read(int(slovnik["Content-length"]))
        sprava_naz = hashlib.md5(sprava_obs.encode()).hexdigest()

        with open(f'{slovnik["Mailbox"]}/{sprava_naz}', "w") as message_file:
            message_file.write(sprava_obs)

    except FileNotFoundError:
        status_code, status_msg = (203, 'No such mailbox')
    except KeyError:
        status_code, status_msg = (200, 'Bad request')
    except ValueError:
        status_code, status_msg = (200, 'Bad request')

    return (header_c, reply_c, status_code, status_msg)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 9999))
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
s.listen(5)

while True:
    connected_socket, address = s.accept()
    print(f'spojenie z {address}')
    pid_chld = os.fork()
    if pid_chld == 0:
        s.close()
        f = connected_socket.makefile(mode='rw', encoding='utf-8')

        while True:
            header_c = ""
            reply_c = ""
            headers_d = {}

            metoda = f.readline().strip()
            if not metoda:
                break

            data = f.readline()

            while data != "\n":
                pomoc = 0
                line = data.strip()
                if line.find(" ") != -1:
                    head_h, content_h = ("", "")
                    pomoc += 1
                if not line.isascii():
                    head_h, content_h = ("", "")
                    pomoc += 1
                try:
                    line = line.split(":")
                except:
                    head_h, content_h = ("", "")
                    pomoc += 1
                if len(line) != 2:
                    head_h, content_h = ("", "")
                    pomoc += 1
                if (line[0].find("/") != -1):
                    head_h, content_h = ("", "")
                    pomoc += 1
                if (pomoc == 0):
                    head_h = line[0]
                    content_h = line[1]

                headers_d[head_h] = content_h
                data = f.readline()

            if len(headers_d) > 2:
                status_code, status_msg = (200, 'Bad request')


            for i in headers_d:
                if i == "" or headers_d[i] == "":
                    status_code, status_msg = (200, 'Bad request')

            status_code, status_ms = (100, 'OK')

            if status_code == 100:

                print("metoda: ", metoda)
                if metoda == 'READ':
                    header_c, reply_c, status_code, status_msg = metoda_citanie(headers_d)

                elif metoda == 'LS':
                    header_c, reply_c, status_code, status_msg = metoda_ls(headers_d)

                elif metoda == 'WRITE':
                    header_c, reply_c, status_code, status_msg = metoda_pisanie(headers_d, f)

                else:
                    status_code, status_msg = (204, 'Unknown method')

                    f.write(f'{status_code} {status_msg}\n')
                    f.write('\n')
                    f.flush()
                    sys.exit(0)

            f.write(f'{status_code} {status_msg}\n')
            f.write(header_c)
            f.write('\n')
            f.write(reply_c)
            f.flush()
        print(f'{address} uzavrel spojenie')
        sys.exit(0)
    else:
        connected_socket.close()