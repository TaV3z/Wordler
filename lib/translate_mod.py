from deep_translator import GoogleTranslator

def translate(word):
    return GoogleTranslator(source='auto', target='ru').translate(word)

