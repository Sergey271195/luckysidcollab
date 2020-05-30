CATEGORY_CHOICES = [
    ('FD', 'Продукты'),
    ('SV', "Услуги"), 
    ('AP', 'Техника'),
    ('PT', 'АЗС'),
    ('RT',  'Рестораны'),
    ### Work in progress
]

STARTING_CHOICES = [
    ('stats', 'Статистика за текущую неделю'),
    ('bar', 'Столбчатая диаграмма'),
    ('pie', 'Круговая диаграмма'), 
    ### Work in progress
]

TIMEPERIOD_CHOICES = [
    ('WC', 'За текущую неделю'),
    ('WL', 'За прошлую неделю'),
    ('MC', 'За текущий месяц'),
    ('ML', 'За прошлый месяц'),
    ('YC', 'За текущий год'),
    ### Work in progress
]


CALLBACK_MESSAGES = [
    'Выберите категорию затрат',
    'Формат предоставления данных',
    'Выберите временной интервал для построения столбчатой диаграммы',
    'Выберите временной интервал для построения круговой диаграммы'
    ### Work in progress
]


GREETING_OPTIONS = [
'Здравствуйте, команда Lavanda$_Bot \
приветствует вас!\nНаш бот поможет вам вести статистику ваших \
расходов и выдавать вам её в виде удобных графиков.'
### Work in progress
]

HELP_MESSAGE = [
'Этот бот создан для сохранения и отражения информации о ваших затратах.\n\
Используйте следующие команды для работы с ботом:\n\
/add - Для того что-бы добавить информацию о ваших тратах воспользуйтесь этой командой\n\
/stat - Эта команда выводит статистику ваших основных трат, а также трат за месяц/год\n\
/datavisualization - Посмотрите удобную диаграмму и график затрат, составленные ботом'

]

WEEKDAYS = [
    'Понедельник', 
    'Вторник',
    'Среда',
    'Четверг',
    'Пятница',
    'Суббота',
    'Воскресенье'

    ### At least this one is finished...
]