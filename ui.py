from pybotx import BubbleMarkup, KeyboardMarkup


#кнопки старта
start = BubbleMarkup()
start.add_button(command="/start", label="Начать чат с ИИ")
start.add_button(command="/help", label="Доступные команды", new_row=False)

#кнопки окончания
end = BubbleMarkup()
end.add_button(command="/end", label="Закончить диалог")
end.add_button(command="/help", label="Доступные команды", new_row=False)

#кнопки остановки генерации
stop = KeyboardMarkup()
stop.add_button(command="/_stop", label="Остановить генерацию")