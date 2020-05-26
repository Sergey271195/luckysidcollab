import json

class InlineKeyobardButton():

    def __init__(self, text, callback_data):

        self.text = text
        self.callback_data = callback_data
    
    def getButton(self):

        return ({'text': self.text, 'callback_data': self.callback_data})



class InlineKeyobardMarkup():

    def __init__(self):
        self.allrows = []

    def getKeyboard(self):

        return(json.dumps({'inline_keyboard': self.allrows}, indent=4))

    def addRow(self, row):
        self.allrows.append(row)


def createRowKeyboard(keyboard_layout):

    keyboard = InlineKeyobardMarkup()

    for category in keyboard_layout:
        button = InlineKeyobardButton(text = category[1], callback_data= category[0]).getButton()
        keyboard.addRow([button])
        
    return keyboard.getKeyboard()

if __name__ == '__main__':
    createCategoryKeyboard()

    



