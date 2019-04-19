import socketserver
from redis import Redis


def to_bulk_str(string):
    """
    Pythonの文字列をバルク文字列に変換する
    """
    b_str = (string + '\r\n').encode()
    b_str_len = len(b_str)
    b_str = ('$' + str(b_str_len - 2) + '\r\n').encode() + b_str
    return b_str


def to_err_message(string):
    """
    エラーメッセージを作る
    """
    return ('-Error ' + string + '\r\n').encode()


def to_simple_str(string):
    """
    シンプル文字列を作る
    """
    return ('+' + string + '\r\n').encode()


def to_int_str(num):
    """
    数値をintegerの文字列に変換する
    """
    return (':' + str(num) + '\r\n').encode()


def is_natural_num(string):
    """
    stringが10進数の整数であるかどうか判定する
    """
    return string.isdecimal() or (string[0] == '-' and string[1:].isdecimal())


redis = Redis(host='redis', port=6379)
data_dict = {}
SIMPLE_OK = b'+OK\r\n'
BULK_NULL = b'$-1\r\n'

ERR_SYNTAX_ERROR = to_err_message('ERR Syntax Error')


class RESPRequestHandler(socketserver.StreamRequestHandler):

    def always_null_response(self):
        return b'$-1\r\n'

    def always_error_response(self):
        err_msg = '-NotImplementedError >>まだ実装されていません<<\r\n'.encode()
        return err_msg

    def accept_int(self):
        """
        RESPのintegerを1つ読み込み、値を返す
        """
        line = self.rfile.readline()
        num = int(line[1:])
        return num

    def accept_bulk_str(self):
        """
        RESPのバルク文字列を1つ読み込み、値を返す
        """
        line = self.rfile.readline().decode()
        # \r\nの2文字分を削る
        bulk_str = line[:-2]
        return bulk_str

    def simple_parser(self, cmd_type, cmd_values):
        response = b'$-1\r\n'

        cmd = cmd_type.upper()
        print(cmd, cmd_values)
        value_len = len(cmd_values)

        # PINGコマンド
        if cmd == 'PING':
            # messageがない場合、PONGのシンプル文字列を返す
            if value_len == 0:
                response = to_simple_str('PONG')
            # messageがある場合、そのメッセージのシンプル文字列を返す
            elif value_len == 1:
                response = to_simple_str(cmd_values[0])
            # 2つ以上の場合エラー
            else:
                response = to_err_message(
                    'ERR wrong number of arguments for "ping" command')
        # SETコマンド
        elif cmd == 'SET':
            if value_len == 2:
                key, value = cmd_values
                data_dict[key] = value
                response = SIMPLE_OK
            elif value_len == 3:
                key, value, option = cmd_values
                option = option.upper()
                if option == 'NX':
                    if key in data_dict:
                        response = BULK_NULL
                    else:
                        data_dict[key] = value
                        response = SIMPLE_OK
                elif option == 'XX':
                    if key in data_dict:
                        data_dict[key] = value
                        response = SIMPLE_OK
                    else:
                        response = BULK_NULL
                else:
                    response = ERR_SYNTAX_ERROR
            else:
                response = to_err_message(
                    'ERR wrong number of arguments for "SET" command')
        elif cmd == 'GET':
            if value_len == 1:
                key = cmd_values[0]
                if key in data_dict:
                    value = data_dict[key]
                    response = to_bulk_str(value)
                else:
                    response = BULK_NULL
            else:
                response = to_err_message(
                    'ERR wrong number of arguments for "GET" command')
        elif cmd == 'DEL':
            if value_len >= 1:
                num_removed_keys = 0
                for key in cmd_values:
                    if key in data_dict:
                        del data_dict[key]
                        num_removed_keys += 1
                response = to_int_str(num_removed_keys)

            else:
                response = ERR_SYNTAX_ERROR
        elif cmd == 'EXISTS':
            if value_len >= 1:
                num_exists_keys = 0
                for key in cmd_values:
                    if key in data_dict:
                        num_exists_keys += 1
                response = to_int_str(num_exists_keys)

            else:
                response = ERR_SYNTAX_ERROR
        elif cmd == 'INCRBY':
            if value_len == 2:
                key, incr = cmd_values
                # incrがintegerかどうか判定
                if is_natural_num(incr):
                    # keyが格納済みかどうかで分岐
                    if key in data_dict:
                        value_str = data_dict[key]
                        # 格納済みの値がintegerかどうか判定
                        if is_natural_num(value_str):
                            value = int(value_str) + int(incr)
                            data_dict[key] = str(value)
                            response = to_int_str(value)
                        else:
                            response = to_err_message(
                                'ERR value is not an integer or out of range')
                    else:
                        value_str = incr
                        data_dict[key] = value_str
                        response = to_int_str(int(value_str))
                else:
                    response = to_err_message(
                        'ERR value is not an integer or out of range')
            else:
                response = ERR_SYNTAX_ERROR

        elif cmd == 'INCR':
            if value_len == 1:
                key = cmd_values[0]

                # keyが格納済みかどうかで分岐
                if key in data_dict:
                    value_str = data_dict[key]
                    # 格納済みの値がintegerかどうか判定
                    if is_natural_num(value_str):
                        value = int(value_str) + 1
                        data_dict[key] = str(value)
                        response = to_int_str(value)
                    else:
                        response = to_err_message(
                            'ERR value is not an integer or out of range')
                else:
                    value_str = '1'
                    data_dict[key] = value_str
                    response = to_int_str(int(value_str))
            else:
                response = ERR_SYNTAX_ERROR
        elif cmd == 'DECRBY':
            if value_len == 2:
                key, decr = cmd_values
                # incrがintegerかどうか判定
                if is_natural_num(decr):
                    # keyが格納済みかどうかで分岐
                    if key in data_dict:
                        value_str = data_dict[key]
                        # 格納済みの値がintegerかどうか判定
                        if is_natural_num(value_str):
                            value = int(value_str) - int(decr)
                            data_dict[key] = str(value)
                            response = to_int_str(value)
                        else:
                            response = to_err_message(
                                'ERR value is not an integer or out of range')
                    else:
                        value_str = decr
                        data_dict[key] = value_str
                        response = to_int_str(int(value_str))
                else:
                    response = to_err_message(
                        'ERR value is not an integer or out of range')
            else:
                response = ERR_SYNTAX_ERROR

        elif cmd == 'DECR':
            if value_len == 1:
                key = cmd_values[0]

                # keyが格納済みかどうかで分岐
                if key in data_dict:
                    value_str = data_dict[key]
                    # 格納済みの値がintegerかどうか判定
                    if is_natural_num(value_str):
                        value = int(value_str) - 1
                        data_dict[key] = str(value)
                        response = to_int_str(value)
                    else:
                        response = to_err_message(
                            'ERR value is not an integer or out of range')
                else:
                    value_str = '-1'
                    data_dict[key] = value_str
                    response = to_int_str(int(value_str))
            else:
                response = ERR_SYNTAX_ERROR
        else:
            response = to_err_message(
                'ERR Unknown or disabled command "{0}"'.format(cmd))
        # print(data_dict)

        return response

    def simple_impl_response(self):

        # 配列の長さ指定とintegerは異なるがチェックしてないので使い回す、後でちゃんと実装する
        array_length = self.accept_int()
        print(array_length)

        cmd_type = None
        cmd_values = []

        #　配列の各要素を受け取る
        for i in range(array_length):
            # 文字列の長さを取得
            str_length = self.accept_int()

            # バルク文字列を取得
            bulk_str = self.accept_bulk_str()
            print(str_length, bulk_str)

            if i == 0:
                cmd_type = bulk_str
            else:
                cmd_values.append(bulk_str)

        response = self.simple_parser(cmd_type, cmd_values)

        # return self.always_null_response()
        return response

    def handle(self):
        print('Recieved:')

        # create response
        response = self.simple_impl_response()

        print('Response:')
        print(response, flush=True)

        # send response
        self.wfile.write(response)
