#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# import base64
import math
import time

sbox = [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16]

rcon = [[0x00, 0x00, 0x00, 0x00],
        [0x01, 0x00, 0x00, 0x00],
        [0x02, 0x00, 0x00, 0x00],
        [0x04, 0x00, 0x00, 0x00],
        [0x08, 0x00, 0x00, 0x00],
        [0x10, 0x00, 0x00, 0x00],
        [0x20, 0x00, 0x00, 0x00],
        [0x40, 0x00, 0x00, 0x00],
        [0x80, 0x00, 0x00, 0x00],
        [0x1b, 0x00, 0x00, 0x00],
        [0x36, 0x00, 0x00, 0x00]]


class AesCtrV2:
    b64code = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="

    def encode_base64(self, plain):
        pad = ''
        e = []
        c = len(plain) % 3
        if c > 0:
            while c < 3:
                pad += "="
                plain += '\0'
                c += 1

        for i in range(0, len(plain), 3):
            o1 = ord(plain[i])
            o2 = ord(plain[i + 1])
            o3 = ord(plain[i + 2])

            bits = o1 << 16 | o2 << 8 | o3

            h1 = bits >> 18 & 0x3f
            h2 = bits >> 12 & 0x3f
            h3 = bits >> 6 & 0x3f
            h4 = bits & 0x3f

            e.append(self.b64code[h1] + self.b64code[h2] + self.b64code[h3] + self.b64code[h4])

        coded = "".join(e)
        coded = coded[0:(len(coded) - len(pad))] + pad
        return coded

    def decode_base64(self, coded):
        d = []

        for i in range(0, len(coded), 4):
            h1 = self.b64code.find(coded[i])
            h2 = self.b64code.find(coded[i + 1])
            h3 = self.b64code.find(coded[i + 2])
            h4 = self.b64code.find(coded[i + 3])

            bits = h1 << 18 | h2 << 12 | h3 << 6 | h4

            o1 = bits >> 16 & 0xff
            o2 = bits >> 8 & 0xff
            o3 = bits & 0xff

            if h3 == 0x40:
                d.append(chr(o1))
            elif h4 == 0x40:
                d.append(chr(o1) + chr(o2))
            else:
                d.append(chr(o1) + chr(o2) + chr(o3))

        plain = "".join(d)
        return plain

    def decrypt_message(self, ciphertext, password, bits=128):
        block_size = 16
        if bits not in [128, 192, 256]:
            return ''
        ciphertext = self.decode_base64(ciphertext)

        bits = int(bits / 8)
        password = [ord(item) for item in password]
        if len(password) >= bits:
            password = password[:bits]
        else:
            add_data = [0] * (bits - len(password))
            password = password + add_data
        key = self.cipher(password, self.key_expansion(password))
        key = key + key[:bits - 16]

        counter_block = [0] * block_size
        ctr_txt = ciphertext[:8]
        for i in range(8):
            counter_block[i] = ord(ctr_txt[i])

        key_schedule = self.key_expansion(key)
        block_count = math.ceil((len(ciphertext) - 8) / block_size)
        cipher_txt = [0] * block_count
        for i in range(block_count):
            cipher_txt[i] = ciphertext[8 + i * block_size: 8 + i * block_size + block_size]

        ciphertext = cipher_txt
        plain_txt = [0] * len(ciphertext)
        for i in range(block_count):
            for j in range(4):
                counter_block[15 - j] = (i >> j * 8) & 0xff
            for j in range(4):
                counter_block[15 - j - 4] = (int((i + 1) / 0x100000000) >> j * 8) & 0xff
            cipher_cntr = self.cipher(counter_block, key_schedule)
            plain_char = [0] * len(ciphertext[i])
            for j in range(len(ciphertext[i])):
                plain_char[j] = cipher_cntr[j] ^ ord(ciphertext[i][j])
                plain_char[j] = chr(plain_char[j])

            plain_txt[i] = "".join(plain_char)

        plaintxt = "".join(plain_txt)
        return plaintxt

    # 加密
    def encrypt_message(self, plaintext, password, bits=128):
        block_size = 16
        if bits not in [128, 192, 256]:
            return ''

        bits = int(bits / 8)
        password = [ord(item) for item in password]
        if len(password) >= bits:
            password = password[:bits]
        else:
            add_data = [0] * (bits - len(password))
            password = password + add_data
        key = self.cipher(password, self.key_expansion(password))
        key = key + key[:bits - 16]

        nonce = int(time.time()) * 1000
        # nonce = 1682396481587
        nonce_sec = math.floor(nonce / 1000)
        nonce_ms = nonce % 1000

        counter_block = [0] * block_size
        for i in range(4):
            counter_block[i] = (nonce_sec >> i * 8) & 0xff

        for i in range(4):
            counter_block[i + 4] = nonce_ms & 0xff

        ctr_txt = ''
        for i in range(8):
            ctr_txt += chr(counter_block[i])
        key_schedule = self.key_expansion(key)
        block_count = math.ceil(len(plaintext) / block_size)
        cipher_txt = [0] * block_count
        for i in range(block_count):
            for j in range(4):
                counter_block[15 - j] = (i >> j * 8) & 0xff
            for j in range(4):
                counter_block[15 - j - 4] = (int(i / 0x100000000) >> j * 8)
            cipher_cntr = self.cipher(counter_block, key_schedule)
            if i < block_count - 1:
                block_length = block_size
            else:
                block_length = (len(plaintext) - 1) % block_size + 1
            cipher_char = [0] * block_length
            for j in range(block_length):
                cipher_char[j] = cipher_cntr[j] ^ ord(plaintext[i * block_size + j])
                cipher_char[j] = chr(cipher_char[j])

            cipher_txt[i] = "".join(cipher_char)

        ciphertext = ctr_txt + "".join(cipher_txt)

        return self.encode_base64(ciphertext)

    def cipher(self, input_bytes, w):
        nb = 4
        nr = int(len(w) / nb) - 1
        state = [[], [], [], []]
        for i in range(4 * nb):
            state[i % 4].append(input_bytes[i])

        state = self.add_round_key(state, w, 0, nb)
        for i in range(1, nr):
            state = self.sub_bytes(state, nb)
            state = self.shift_rows(state, nb)
            state = self.min_columns(state, nb)
            state = self.add_round_key(state, w, i, nb)

        state = self.sub_bytes(state, nb)
        state = self.shift_rows(state, nb)
        state = self.add_round_key(state, w, nr, nb)

        output = []
        for i in range(4 * nb):
            output.append(state[i % 4][math.floor(i / 4)])
        return output

    @staticmethod
    def add_round_key(state, w, rnd, nb):
        for i in range(4):
            for j in range(nb):
                state[i][j] ^= w[rnd * 4 + j][i]
        return state

    @staticmethod
    def sub_bytes(state, nb):
        for i in range(4):
            for j in range(nb):
                state[i][j] = sbox[state[i][j]]
        return state

    @staticmethod
    def shift_rows(state, nb):
        for i in range(1, 4):
            temp = []
            for j in range(nb):
                temp.append(state[i][(j + i) % nb])
            for j in range(nb):
                state[i][j] = temp[j]
        return state

    @staticmethod
    def min_columns(state, nb):
        for i in range(4):
            a = []
            b = []
            for j in range(nb):
                a.append(state[j][i])
                if state[j][i] & 0x80:
                    b.append(state[j][i] << 1 ^ 0x011b)
                else:
                    b.append(state[j][i] << 1)
            state[0][i] = b[0] ^ a[1] ^ b[1] ^ a[2] ^ a[3]
            state[1][i] = a[0] ^ b[1] ^ a[2] ^ b[2] ^ a[3]
            state[2][i] = a[0] ^ a[1] ^ b[2] ^ a[3] ^ b[3]
            state[3][i] = a[0] ^ b[0] ^ a[1] ^ a[2] ^ b[3]
        return state

    def key_expansion(self, key):
        nb = 4
        nk = int(len(key) / 4)
        nr = nk + 6

        w = [[]] * (nb * (nr + 1))
        for i in range(nk):
            w[i] = [key[4 * i], key[4 * i + 1], key[4 * i + 2], key[4 * i + 3]]

        for i in range(nk, (nb * (nr + 1))):
            temp = []
            for j in range(4):
                temp.append(w[i - 1][j])

            if i % nk == 0:
                temp = self.sub_word(self.rot_word(temp))
                for j in range(4):
                    temp[j] ^= rcon[int(i / nk)][j]
            elif nk > 6 and i % nk == 4:
                temp = self.sub_word(temp)

            wi = []
            for j in range(4):
                wi.append(w[i - nk][j] ^ temp[j])
            w[i] = wi

        return w

    @staticmethod
    def sub_word(w):
        for i in range(4):
            w[i] = sbox[w[i]]
        return w

    @staticmethod
    def rot_word(w):
        tmp = w[0]
        for i in range(3):
            w[i] = w[i + 1]
        w[3] = tmp
        return w
