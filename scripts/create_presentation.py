#!/usr/bin/env python3
"""Create PPTX presentation about ABS vs PLA vs PETG comparison."""
import sys
import os
sys.path.insert(0, '.')

from skills.slides.skill import create_slide_deck, export_to_pptx

# Define slides as structured data
slides = [
    {
        "type": "title",
        "title": "Сравнение материалов для 3D печати",
        "subtitle": "ABS vs PLA vs PETG",
        "content": "Характеристики, цены и рекомендации по применению\n\nАктуально на май 2025 | Данные: Ozon, Wildberries, 3DTool, 3DTech"
    },
    {
        "type": "content",
        "title": "Обзор материалов",
        "content": "Таблица базовых характеристик:\n\n• PLA (Полилактид): плотность 1.24 г/см³, Tg 55-60°C, печать 190-220°C\n• ABS (Акрилонитрилбутадиенстирол): плотность 1.04 г/см³, Tg 105°C, печать 220-250°C\n• PETG (Полиэтилентерефталатгликоль): плотность 1.27 г/см³, Tg 75-80°C, печать 220-250°C\n\nPLA не требует нагреваемого стола, ABS требует 90-110°C, PETG рекомендует 70-80°C"
    },
    {
        "type": "content", 
        "title": "Механические характеристики",
        "content": "Сравнение прочности и свойств:\n\n• Прочность на растяжение:\n  - PLA: 50-60 МПа (самый жесткий)\n  - ABS: 40-50 МПа\n  - PETG: 50-60 МПа\n\n• Удлинение при разрыве:\n  - PLA: 3-5% (хрупкий)\n  - ABS: 10-25% (гибкий)\n  - PETG: 15-30% (самый ударостойкий)\n\n• Влагопоглощение:\n  - PETG: 0.2% (лучший)\n  - ABS: 0.3%\n  - PLA: 0.5%"
    },
    {
        "type": "content",
        "title": "Безопасность и экология",
        "content": "Важно для печати в жилых помещениях:\n\n• Токсичность при печати:\n  - PLA: низкая, безопасен\n  - ABS: высокая, выделяет пары (нужна вентиляция!)\n  - PETG: низкая, безопасен\n\n• Запах:\n  - PLA: приятный (попкорн)\n  - ABS: резкий (пластик)\n  - PETG: почти нет\n\n• Пищевая безопасность: PLA и PETG — да, ABS — нет\n• Биоразлагаемость: только PLA\n• УФ-стойкость: ABS лучший, PETG средний, PLA низкий"
    },
    {
        "type": "content",
        "title": "Цены в России (2024-2025)",
        "content": "Реальные цены с маркетплейсов:\n\nБюджетный сегмент (Ozon/Wildberries):\n• PLA: 650-950 руб/кг\n• ABS: 800-1200 руб/кг\n• PETG: 750-1150 руб/кг\n\nСредний сегмент (Bestfilament, 3DTech):\n• PLA: 950-1100 руб/кг\n• ABS: 1200-1700 руб/кг\n• PETG: 1150-1400 руб/кг\n\nПремиум (ColorFabb, Prusament):\n• PLA: 2200 руб/кг\n• ABS: 2500 руб/кг\n• PETG: 2400 руб/кг\n\nВывод: PLA дешевле на 15-20%"
    },
    {
        "type": "content",
        "title": "Рекомендации по применению",
        "content": "Когда что использовать:\n\n• PLA — для начинающих, прототипов, декора, пищевых контейнеров\n  Простая печать, безопасен, биоразлагаем\n\n• ABS — для автозапчастей, уличных конструкций, термостойких деталей\n  Требует камеры с вентиляцией и нагреваемого стола\n\n• PETG — золотая середина! Кухня, ванная, функциональные детали\n  Прочность ABS + безопасность PLA + влагостойкость"
    },
    {
        "type": "content",
        "title": "Сводная матрица выбора",
        "content": "Рейтинг по критериям (1-5 звезд):\n\n• Простота печати: PLA ★★★★★ | PETG ★★★★☆ | ABS ★★☆☆☆\n• Прочность: PETG ★★★★★ | ABS ★★★★☆ | PLA ★★★☆☆\n• Термостойкость: ABS ★★★★★ | PETG ★★★☆☆ | PLA ★★☆☆☆\n• Безопасность: PLA ★★★★★ | PETG ★★★★★ | ABS ★★☆☆☆\n• Ударостойкость: PETG ★★★★★ | ABS ★★★★☆ | PLA ★★☆☆☆\n• Влагостойкость: PETG ★★★★★ | ABS ★★★☆☆ | PLA ★★☆☆☆\n• Цена: PLA ★★★★★ | PETG ★★★★☆ | ABS ★★★☆☆"
    },
    {
        "type": "title",
        "title": "Итоги и выводы",
        "subtitle": "Выбор материала под задачу",
        "content": "PLA — лучший для начинающих и декора. Безопасен, дешев, биоразлагаем.\n\nABS — для профи: термостойкость, УФ-защита, прочность. Требует камеры.\n\nPETG — золотая середина! Прочность ABS + безопасность PLA.\n\nСоздано с помощью My Agent AI | NeuroAPI + OpenRouter + Tavily | Май 2025"
    }
]

# Create deck
deck = create_slide_deck(
    title="Сравнение ABS PLA PETG для 3D печати",
    slides=slides,
    theme={
        "primary": "#1F4E78",
        "secondary": "#2E75B6",
        "background": "#ffffff",
        "text": "#1f2937",
        "accent": "#C55A11",
        "font_heading": "Segoe UI, sans-serif",
        "font_body": "Segoe UI, sans-serif"
    }
)

print(f'Deck created: {deck["title"]}')
print(f'Slides: {deck["slide_count"]}')

# Save HTML
html_path = 'output/presentation_ABS_PLA_PETG.html'
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(deck['html'])
print(f'HTML saved: {html_path}')

# Export to PPTX
pptx_path = 'output/презентация_ABS_PLA_PETG.pptx'
result = export_to_pptx(deck, pptx_path)

if result.startswith('Error'):
    print(f'PPTX export issue: {result}')
    print('HTML version is ready!')
else:
    print(f'PPTX created: {result}')
    size = os.path.getsize(result)
    print(f'Size: {size:,} bytes ({size/1024:.1f} KB)')
    
print()
print('=== FILES CREATED ===')
print(f'1. {os.path.abspath(html_path)}')
if not result.startswith('Error'):
    print(f'2. {os.path.abspath(result)}')
