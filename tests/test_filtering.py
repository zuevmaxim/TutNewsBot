import unittest

from ai.ai import should_skip_text


class TestFiltering(unittest.TestCase):
    def test_should_not_skip(self):
        self.assertFalse(should_skip_text("""
        Как подготовиться к первому походу, чтобы всё прошло гладко

        Составили подробную инструкцию вместе с национальным проектом «Туризм и индустрия гостеприимства».
        
        https://lh.su/2u0r"""))

    def test_skip_comment_hype_1(self):
        self.assertTrue(should_skip_text("Опишите ваши выходные одним стикером в комментариях 👇"))

    def test_skip_comment_hype_2(self):
        self.assertTrue(should_skip_text("""
        Продолжите фразу в комментариях 👇🏻

        Хочется простого человеческого...
        """))

    def test_skip_emoji_hype_1(self):
        self.assertTrue(should_skip_text("""
        Чем вы обычно завтракаете? 

        ❤️ — чем-нибудь сладким
        👍 — чем-нибудь солёным 
        💅🏻 — как получится 
        🌚 — да кто такой этот ваш завтрак?
        """))

    def test_skip_emoji_hype_2(self):
        self.assertTrue(should_skip_text("""
        Осенний опрос: вы уже достали тёплые вещи? 

        ❤️ — да
        💅🏻 — у меня вообще-то 48-е августа
        🌚 — буду терпеть до последнего зелёного листика
        """))

    def test_should_not_skip_long_messsages(self):
        message = "Что вы делаете по утрам? Оставьте комментарий"
        message = "\n".join(message for _ in range(20))
        self.assertFalse(should_skip_text(message))
