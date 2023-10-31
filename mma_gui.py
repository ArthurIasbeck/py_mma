import tkinter as tk
from tkinter import Entry, Text, Button, Scrollbar, Label
import time
from datetime import datetime

import numpy as np
import turtle

from pymma.mma import MmaDesign


class MmaGui:

    def __init__(self):
        self.screen = None  # Objeto que guarda a janela associada ao pacote turtle
        self.text = None  # Caixa de texto
        self.entries = []  # Lista que contém as entradas do usuário
        self.t = None  # Objeto turtle utilizado no desenho do MMA
        self.first_run = True

    # Função associada ao botão
    def design_mma(self):
        C = np.matrix(self.entries[0].get())
        g_0 = float(self.entries[1].get())
        B_b = float(self.entries[2].get())
        r_r = float(self.entries[3].get())
        f_i = float(self.entries[4].get())
        f_x_0 = float(self.entries[5].get())
        f_y_0 = float(self.entries[6].get())
        f_x_s = float(self.entries[7].get())
        f_y_s = float(self.entries[8].get())
        gamma = float(self.entries[9].get())
        mma = MmaDesign(C, g_0, B_b, r_r, f_i, f_x_0, f_y_0, f_x_s, f_y_s, gamma)
        mma.log_level = 'INFO'
        mma.design(log_results=True)
        mma.draw(save_result=True, turtle=self.t, screen=self.screen)
        if not self.first_run:
            self.text.insert(
                'end',
                '--------------------------------------------------------------------------------\n\n')

        self.text.insert(
            'end',
            f'Iniciando dimensionamento ({datetime.fromtimestamp(time.time()).strftime("%d-%m-%Y %H:%M:%S")})\n\n')
        self.text.insert('end', mma.log_return)
        self.text.insert('end', '\n')
        self.first_run = False

    def build_gui(self):
        # Criação da janela
        window = tk.Tk()

        # Configuração da janela
        window.title("Dimensionamento de MMAs")
        window.columnconfigure(0, weight=1)
        window.columnconfigure(1, weight=1)

        # Criação do frame para a primeira coluna
        frame1 = tk.Frame(window)
        frame1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Criação das colunas em que ficarão os labels e as entradas referentes a eles
        frame1.columnconfigure(0, weight=2, minsize=100)
        frame1.columnconfigure(1, weight=8, minsize=200)

        # Inserção dos labels e das entradas (inseridas nas colunas criadas anteriormente)
        parameters = ['C', 'g_0', 'B_b', 'r_r', 'f_i', 'f_x_0', 'f_y_0', 'f_x_s', 'f_y_s', 'gamma']
        default_parameter_values = ['1, 0, 1; 0, -1, -1; 0, 1, 1; 1, 0, -1; -1, 0, 1; 0, 1, -1; 0, -1, 1;-1 0 -1',
                                    1e-3, 0.6, 40e-3, 0.3697, 0, 500, 75, 75, 1]

        for i, parameter in enumerate(parameters):
            Label(frame1, text=parameter).grid(row=i, column=0, padx=5, pady=5)
            entry = Entry(frame1)
            entry.insert(0, default_parameter_values[i])
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            self.entries.append(entry)

        # Criação do botão para execução do dimensionamento
        Button(frame1, text="Executar dimensionamento", command=self.design_mma).grid(row=len(parameters), column=0,
                                                                                      columnspan=2, padx=5, pady=5)

        # Criação do frame para inserção da caixa de texto e da barra de rolagem
        frame_text = tk.Frame(frame1)
        frame_text.grid(row=len(parameters) + 1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Inserção do texto e da barra de rolagem
        self.text = Text(frame_text)
        self.text.pack(side='left', fill='both', expand=True)
        scrollbar = Scrollbar(frame_text)
        scrollbar.pack(side='right', fill='y')
        self.text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text.yview)

        # Criação do frame para imagem (na segunda coluna)
        frame2 = tk.Frame(window)
        frame2.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        canvas = tk.Canvas(frame2)
        canvas.config(width=1000, height=785)
        canvas.pack(side=tk.LEFT)
        self.screen = turtle.TurtleScreen(canvas)
        self.t = turtle.RawTurtle(self.screen)

        # Inicialização da interface
        window.mainloop()


def main():
    mma_gui = MmaGui()
    mma_gui.build_gui()


if __name__ == '__main__':
    main()
