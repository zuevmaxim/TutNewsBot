import unittest

from ai.ai import should_skip_text

TEXT_MAX_HYPE_TEXT_LENGTH = 500


class TestFiltering(unittest.TestCase):
    def test_should_not_skip_1(self):
        self.assertFalse(should_skip_text("""
        Как подготовиться к первому походу, чтобы всё прошло гладко

        Составили подробную инструкцию вместе с национальным проектом «Туризм и индустрия гостеприимства».
        
        https://lh.su/2u0r""", max_length=TEXT_MAX_HYPE_TEXT_LENGTH))

    def test_should_not_skip_2(self):
        self.assertFalse(should_skip_text("""
        Как сделать микроклимат в квартире безопасным для себя и детей

        Регулярное проветривание не всегда гарантирует, что вы дышите дома чистым воздухом.
        
        https://lh.su/2ud4
        
        😶 Подписаться | Задать вопрос
        """, max_length=TEXT_MAX_HYPE_TEXT_LENGTH))

    def test_should_not_skip_3(self):
        self.assertFalse(should_skip_text("""
        Как наводить порядок в доме без лишних усилий

        Превращаем уборку из обязаловки в приятное занятие.
        
        https://lh.su/2iq2
        
        😶 Подписаться | Задать вопрос
        """, max_length=TEXT_MAX_HYPE_TEXT_LENGTH))

    def test_should_not_skip_4(self):
        self.assertFalse(should_skip_text("Виттория Черетти (26) ❤️\nХороша!"))

    def test_should_not_skip_5(self):
        self.assertFalse(should_skip_text("""
        Как выбрать хороший утюг для дома

        Расскажем, как сэкономить на дополнительных функциях и не испортить вещи.
        
        Читать →
        
        😶 Подписаться | Задать вопрос
        """))

    def test_skip_comment_hype_1(self):
        self.assertTrue(should_skip_text("Опишите ваши выходные одним стикером в комментариях 👇"))

    def test_skip_comment_hype_2(self):
        self.assertTrue(should_skip_text("""
        Продолжите фразу в комментариях 👇🏻

        Хочется простого человеческого...
        """))

    def test_skip_comment_hype_3(self):
        self.assertTrue(should_skip_text("Понедельник. Мнения?"))

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

    def test_skip_emoji_hype_3(self):
        self.assertTrue(should_skip_text("""
        В каком вы клубе?

        ❤️ — доставки 
        💅🏻 — готовка 
        🌚 — зависит от настроения
        """))

    def test_should_not_skip_long_messsages(self):
        message = "Что вы делаете по утрам? Оставьте комментарий"
        message = "\n".join(message for _ in range(20))
        self.assertFalse(should_skip_text(message))
