import requests


class sendSms:
    def sendsms(self, code, mobile_number):
        print(code,mobile_number,'from sms file')
        r = requests.post('http://aakashsms.com/admin/public/sms/v1/send',
                                    data={'auth_token': '127742dcdda0e4dba2aa5ae33f96551379bfe4189fcedd5afb4ed3d589dc6b05',
                                'from': '31001', 'to': str(mobile_number), 'text': 'The verification code is ' + code})
        return r
