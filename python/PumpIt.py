#.....................................................................................ПОДГОТОВКА ПРИЛОЖЕНИЯ
#импорт библиотек
from tkinter import *  
from tkinter import ttk
from tkinter.ttk import Combobox
from tkinter.ttk import Checkbutton
from tkinter.ttk import Progressbar
import time
from functools import partial
from threading import Thread
# инициирование глобальных переменных
pressure_act = 0 # измеренное значение давления в насосе
pressure_max = 100 # максимально допустимое значение давления в насосе
lock = False # блокировка Пуск, Стоп
message = '' # информационные сообщения
# настройка окна приложения
window = Tk()
window.title("PumpIt v.1.9")
window.geometry('450x750')
# инициирование переменных TKINTER
# вкладка1
mode = StringVar() # режим
mode.set('Основной')
state = StringVar() # состояние
state.set('Отключен')
voltage = BooleanVar() # наличие напряжения
voltage.set(True)
pressure = IntVar(value=0) # показания давления
wasted = IntVar(value=0) # время запуска/остановки насоса
starter = BooleanVar() # контроль положения магнитного пускателя
starter.set(False)
last_op = StringVar() # последняя активированная команда
last_op.set('')
fail_voltage = BooleanVar() # активация неисправности электрики
fail_voltage.set(False)
fail_starter = BooleanVar() # активация неисправности пускателя
fail_starter.set(False)
f_pressure = IntVar(value=20) # скорость набора давления
# вкладка 2
delay_start = IntVar(value=7) # допустимое время запуска насоса, c
delay_stop = IntVar(value=7) # допустимое время остановки насоса, c
pressure_limit = IntVar(value=50) # нижняя граница допустимого давления включенного насоса, ед
limit_U = IntVar(value=40) # допустимый интервал прерывания напряжения, с


#.....................................................................................СМЕНА РЕЖИМА
def change_mode(event):
    select=combo.get()
# Основной
    if select == 'Основной':
        if (mode.get() == 'Ремонтный') and (state.get() =='Отключен'):
            selftest()
            if state.get() != 'Неисправность':
                mode.set(select)
            else: send_message('УСТАНОВКА РЕЖИМА ЗАБЛОКИРОВАНА')
        elif (mode.get() == 'Ручной') and (state.get() in ['Отключен', 'Включен']):
            selftest()
            if state.get() != 'Неисправность':
                mode.set(select)
            else: send_message('УСТАНОВКА РЕЖИМА ЗАБЛОКИРОВАНА')
        else: send_message('УСТАНОВКА РЕЖИМА ЗАБЛОКИРОВАНА')
# Ручной
    if select == 'Ручной':
        if (mode.get() == 'Ремонтный') and (state.get() =='Отключен'):
            mode.set(select)
        elif (mode.get() == 'Основной') and (state.get() in ['Отключен', 'Включен']):
            mode.set(select)
        else: send_message('УСТАНОВКА РЕЖИМА ЗАБЛОКИРОВАНА')
# Ремонтный
    if select == 'Ремонтный':
        mode.set(select)
        if state.get() != 'Отключен':
            stop_click('op')


#.....................................................................................ТАЙМЕРЫ В ОТДЕЛЬНЫХ ПОТОКАХ
#.....................................................................................Таймер отсутствия напряжения
def timer_U():
    global timer_stop
    time.sleep(limit_U.get())
    selftest()
    if mode.get() in ['Основной', 'Ручной']:
        timer_stop = time.time()
        autostop()
#.....................................................................................Таймер блокировки клавиш Пуск, Стоп
def timer_lock():
    global lock
    lock = True
    time.sleep(1)
    lock = False
#.....................................................................................Таймер информационных сообщений
def timer_message():
    global message
    display.configure(text=message)
    time.sleep(2)
    display.configure(text='')
#.....................................................................................Таймер автостопа
def timer_autostop():
    time.sleep(3)
    autostop()


#.....................................................................................СЕРВИСЫ
#.....................................................................................Отправка информационных сообщений
def send_message(arg):
        global message
        message = arg
        send = Thread(target=timer_message, args=())
        send.start()
#.....................................................................................Постоянный автостоп
def autostop():
    global pressure_act, timer_stop
    if (state.get()== 'Неисправность') and (mode.get()!= "Ручной"):
        starter.set(False)
        send_message('АВТОСТОП')
        while (pressure_act > 0):
            time.sleep(1)
            pressure_act -= int(f_pressure.get())
            pressure.set(pressure_act)
            bar['value'] = pressure_act
            wasted.set(int((time.time() - timer_stop)))
            window.update()
    if state.get()== 'Неисправность':
        a_stop = Thread(target=timer_autostop, args=())
        a_stop.start()


#.....................................................................................ОТКАЗЫ
#.....................................................................................неисправность электрики
def off_electric():
    global timer_stop
    if fail_voltage.get() == True:
        voltage.set(False)
    else:
        voltage.set(True)
# Отказ электрики        
# Кратковременное прерывание напряжения отключенного насоса
    if (state.get() == 'Отключен') and (voltage.get() == False):
        th = Thread(target=timer_U, args=())
        th.start()
        return
# Прерывание напряжения при работе насоса
    else:
        selftest()
        if mode.get() == 'Основной':
            mode.set('Ремонтный')
            timer_stop = time.time()
            autostop()
#.....................................................................................установка скорости набора/сброса давления
def off_speed(event):
    global pressure_speed, timer_stop
    pressure_speed=int(f_pressure.get())
#.....................................................................................неисправность магнитного пускателя
def off_starter():
    global timer_stop
    if fail_starter.get() == True:
        starter.set(False)
        selftest()
        if mode.get() == 'Основной':
            mode.set('Ремонтный')
            timer_stop = time.time()
            autostop()


#.....................................................................................RESET
def reset():
    state.set('Отключен')


#.....................................................................................REBOOT
def reboot():
    global pressure_act
    pressure_act=0
    state.set('Отключен')
    mode.set('Основной')
    last_op.set('')
    fail_voltage.set(False)
    fail_starter.set(False)
    f_pressure.set(10)
    starter.set(False)
    voltage.set(True)
    pressure.set(0)
    combo.set('Основной')
    bar['value'] = 0
    wasted.set(0)

#.....................................................................................КОНТРОЛЬ ТЕКУЩЕГО СОСТОЯНИЯ
def selftest():
    if state.get() == 'Отключен':
        if (voltage.get() == False) or (starter.get() == True) or (pressure.get() > 0):
            state.set('Неисправность')
            return
    if state.get() == 'Запускается':
        if (voltage.get() == False) or (starter.get() == False) or (pressure.get() == 0):
            state.set('Неисправность')
            return
    if state.get() == 'Включен':
        if (voltage.get() == False) or (starter.get() == False) or (pressure.get() == 0):
            state.set('Неисправность')
            return
    if state.get() == 'Останавливается':
        if (voltage.get() == False) or (starter.get() == True) or (pressure.get() == 0):
            state.set('Неисправность')
            return
    if fail_starter.get() == True:
            state.set('Неисправность')
            return


#.....................................................................................СТАРТ
def start_click(arg):
    global pressure_act, pressure_max, lock, timer_stop
# Блокировка непрерывного пуска
    if lock == True:
        send_message('НЕПРЕРЫВНЫЙ ПУСК ЗАПРЕЩЁН')
        return
    th = Thread(target=timer_lock, args=())
    th.start()
# Блокировка пуска
    if state.get() in ['Включен', 'Запускается']:
        send_message('ПУСК ЗАПРЕЩЁН ПРИ РАБОТЕ НАСОСА')
        return
    if (arg == 'op') and (mode.get() != 'Основной'):
        send_message('ПУСК ЗАПРЕЩЁН')
        return
    if (arg == 'loc') and (mode.get() == 'Ремонтный'):
        send_message('ПУСК ЗАПРЕЩЁН')
        return
# контроль текущего состояния
    selftest()
# Проверка возможности запуска
    if ((state.get()=='Неисправность') or (fail_starter.get() == True)) and (mode.get() != 'Ручной'):
        state.set('Неисправность')
        mode.set('Ремонтный')
# аварийный останов
        timer_stop = time.time()
        autostop()
        return
    if arg == 'op': last_op.set('Пуск от оператора')
    else: last_op.set('Пуск по месту')
# запуск насоса
    timer_start = time.time()
    if state.get() != 'Неисправность': state.set('Запускается')
    starter.set(True)
    window.update()
# набор давления в цикле
    while (pressure_act < pressure_max) and (last_op.get() in ['Пуск от оператора', 'Пуск по месту']):
        time.sleep(1)
        pressure_act += int(f_pressure.get())
        pressure.set(pressure_act)
        bar['value'] = pressure_act
        wasted.set(int((time.time() - timer_start)))
        window.update()
# мониторинг и проверка на включенное состояние
        selftest()
        if (state.get()== 'Неисправность') and (mode.get()!= 'Ручной'):
# аварийный останов
            timer_stop = time.time()
            autostop()
            break
        if (state.get()== 'Запускается') and  (pressure_act > int(pressure_limit.get())):
            state.set('Включен')
            window.update()
# проверка на невыход в рабочий режим за допустимое время            
        if ((time.time() - timer_start) > int(delay_start.get())) and (state.get()!='Включен') and (mode.get()!= 'Ручной') and (last_op.get() in ['Пуск от оператора', 'Пуск по месту']):
#            wasted.set(int((time.time() - timer_start)))
            state.set('Неисправность')
            mode.set('Ремонтный')
# аварийный останов
            timer_stop = time.time()
            autostop()
            break
        if ((time.time() - timer_start) > int(delay_start.get())) and (state.get()!='Включен') and (mode.get()== 'Ручной') and (last_op.get() in ['Пуск от оператора', 'Пуск по месту']):
            state.set('Неисправность')
    return


#.....................................................................................СТОП
def stop_click(arg):
    global pressure_act, pressure_max, lock, timer_stop
# Блокировка непрерывного стопа
    if lock == True:
        send_message('НЕПРЕРЫВНЫЙ СТОП ЗАПРЕЩЁН')
        return
    th = Thread(target=timer_lock, args=())
    th.start()
# Блокировка останова
    if state.get() in ['Отключен', 'Останавливается']:
        send_message('СТОП ЗАПРЕЩЁН ПРИ ОТКЛЮЧЕНИИ')
        return
# контроль текущего состояния
    selftest()
# Подготовка к останову
    if (state.get()=='Неисправность') and (mode.get() != 'Ручной'):
        mode.set('Ремонтный') 
    if arg == 'op': last_op.set('Стоп от оператора')
    else: last_op.set('Стоп по месту')
# останов насоса
    if state.get() != 'Неисправность': state.set('Останавливается')
    starter.set(False)
    timer_stop = time.time()
    window.update()
# сброс давления в цикле
    while (pressure_act > 0) and (last_op.get() in ['Стоп от оператора', 'Стоп по месту']):
        time.sleep(1)
        pressure_act -= int(f_pressure.get())
        pressure.set(pressure_act)
        bar['value'] = pressure_act
        wasted.set(int((time.time() - timer_stop)))
        window.update()
# проверка на отключённое состояние
        if (state.get()== "Останавливается") and  (pressure_act < int(pressure_limit.get())) and (starter.get()==False) and (voltage.get()==True):
            state.set('Отключен')
            window.update()
 # проверка на невыход в рабочий режим за допустимое время             
        if ((time.time() - timer_stop) > int(delay_stop.get())) and (state.get()!='Отключен') and (mode.get()!= 'Ручной') and (last_op.get() in ['Стоп от оператора', 'Стоп по месту']):
            state.set('Неисправность')
            mode.set('Ремонтный')
# аварийный останов
            autostop()
            break
        if ((time.time() - timer_stop) > int(delay_stop.get())) and (state.get()!='Отключен') and (mode.get()== 'Ручной') and (last_op.get() in ['Стоп от оператора', 'Стоп по месту']):
            state.set('Неисправность')
    return


#.....................................................................................ГРАФИЧЕСКИЙ ИНТЕРФЕЙС  
# настройка оконных вкладок
tab_control = ttk.Notebook(window)
tab1 = ttk.Frame(tab_control)
tab2 = ttk.Frame(tab_control)
tab_control.add(tab1, text='Насос')
tab_control.add(tab2, text='Настройки')
#.....................................................................................Графический интерфейс. Вкладка GUI НАСОС
# раздел GUI УПРАВЛЕНИЕ НАСОСОМ
Label(tab1, text='УПРАВЛЕНИЕ', font=("Arial Bold", 13)).grid(column=0, row=0, padx=50, pady=10)
Label(tab1, text='Установка режима').grid(column=0, row=1)
combo = Combobox(tab1)
combo['values'] = ('Основной', 'Ручной', 'Ремонтный')
combo.current(0)
combo.grid(column=1, row=1)
combo.bind('<<ComboboxSelected>>', change_mode)
Label(tab1, text='управление от оператора').grid(column=0, row=2, padx=40, pady=10)
btn_start_op = Button(tab1, text='ПУСК', font=("Arial Bold", 15), fg="green", command=partial(start_click, 'op'))
btn_start_op.grid(column=0, row=3)
btn_stop_op = Button(tab1, text='СТОП', font=("Arial Bold", 15), fg="red", command=partial(stop_click,'op'))
btn_stop_op.grid(column=1, row=3)
Label(tab1, text='управление по месту').grid(column=0, row=4, padx=40, pady=10)
btn_start_loc = Button(tab1, text='ПУСК', font=("Arial Bold", 15), fg="green", command=partial(start_click, 'loc'))
btn_start_loc.grid(column=0, row=5)
btn_stop_loc = Button(tab1, text='СТОП', font=("Arial Bold", 15), fg="red",command=partial(stop_click,'loc'))
btn_stop_loc.grid(column=1, row=5)
# раздел GUI МОНИТОРИНГ ПАРАМЕТРОВ НАСОСА
Label(tab1, text='МОНИТОРИНГ', font=("Arial Bold", 13)).grid(column=0, row=6, padx=50, pady=15)
Label(tab1, text='Режим:').grid(column=0, row=7)
ent_mode = Entry(tab1,width=20, state='disabled', textvariable=mode)
ent_mode.grid(column=1, row=7)
Label(tab1, text='Состояние:').grid(column=0, row=8)
ent_state = Entry(tab1,width=20, state='disabled', textvariable=state)
ent_state.grid(column=1, row=8)
Label(tab1, text='Напряжение:').grid(column=0, row=9)
chk_U = Checkbutton(tab1, state='disabled', var=voltage)
chk_U.grid(column=1, row=9)
Label(tab1, text='Давление, ед:').grid(column=0, row=10)
ent_pressure = Entry(tab1,width=20, state='disabled', textvariable=str(pressure))
ent_pressure.grid(column=1, row=10)
bar = Progressbar(tab1, length=124)
bar.grid(column=1, row=11)
Label(tab1, text='Магнитный пускатель:').grid(column=0, row=13)
chk_starter = Checkbutton(tab1, state='disabled', var=starter)
chk_starter.grid(column=1, row=13)
Label(tab1, text='Прошлая команда:').grid(column=0, row=14)
ent_last_com = Entry(tab1,width=20, state='disabled', textvariable=last_op)
ent_last_com.grid(column=1, row=14)
Label(tab1, text='Время старт/стоп:').grid(column=0, row=15)
ent_time = Entry(tab1,width=20, state='disabled', textvariable=wasted)
ent_time.grid(column=1, row=15)
display = Label(tab1,width=40, text="", fg="red")
display.grid(column=0, row=16)
# раздел GUI ЭМУЛЯЦИЯ НЕИСПРАВНОСТЕЙ НАСОСА
Label(tab1, text='ЭМУЛЯЦИЯ ОТКАЗОВ', font=("Arial Bold", 13)).grid(column=0, row=18, padx=50, pady=15)
Label(tab1, text='Неисправность электрики:').grid(column=0, row=19)
chk_fail_U = Checkbutton(tab1, state='enabled', var=fail_voltage, command=off_electric)
chk_fail_U.grid(column=1, row=19)
Label(tab1, text='Неисправность пускателя:').grid(column=0, row=20)
chk_fail_starter = Checkbutton(tab1, state='enabled', var=fail_starter, command=off_starter)
chk_fail_starter.grid(column=1, row=20)
Label(tab1, text='Скорость набора, ед/c').grid(column=0, row=21)
f_pressure = Combobox(tab1)
f_pressure['values'] = ('5', '10', '20', '25', '50')
f_pressure.current(1)
f_pressure.grid(column=1, row=21)
f_pressure.bind('<<ComboboxSelected>>', off_speed)
btn_reboot = Button(tab1, text='REBOOT', font=("Arial Bold", 15), fg="grey", command=reboot)
btn_reboot.grid(column=0, row=22, pady=40)
btn_reset = Button(tab1, text='RESET', font=("Arial Bold", 15), fg="grey", command=reset)
btn_reset.grid(column=1, row=22, pady=40)
#.....................................................................................Графический интерфейс. Вкладка GUI НАСТРОЙКИ
# раздел GUI НАСТРОЙКИ НАСОСА
Label(tab2, text='НАСТРОЙКИ', font=("Arial Bold", 13)).grid(column=0, row=0, padx=50, pady=10)
Label(tab2, text='Допуск на запуск, с :').grid(column=0, row=2)
ent_delay_start = Entry(tab2,width=5, textvariable=str(delay_start))
ent_delay_start.grid(column=1, row=2)
Label(tab2, text='Допуск на остановку, с :').grid(column=0, row=3)
ent_delay_stop = Entry(tab2,width=5, textvariable=str(delay_stop))
ent_delay_stop.grid(column=1, row=3)
Label(tab2, text='Предел включения, ед :').grid(column=0, row=4)
ent_press_limit = Entry(tab2,width=5, textvariable=str(pressure_limit))
ent_press_limit.grid(column=1, row=4)
Label(tab2, text='Предел прерыввания U, с :').grid(column=0, row=5)
ent_U_limit = Entry(tab2,width=5, textvariable=str(limit_U))
ent_U_limit.grid(column=1, row=5)

tab_control.pack(expand=1, fill='both')
window.mainloop()
