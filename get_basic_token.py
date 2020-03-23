import hashlib


if __name__ == '__main__':
    raw_password = input('input raw password:')
    print('the token is ...')
    print(hashlib.sha512(raw_password.encode()).hexdigest())
