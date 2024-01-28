import time

import numpy as np
import turtle
from datetime import datetime

from src.exceptions.design_exception import DrawWithoutDesignException


def process_kwargs(kwargs, variable_name, default_value):
    if variable_name in kwargs:
        return kwargs[variable_name]
    else:
        return default_value


class Mma:

    def __init__(self, C, g_0, B_b, r_r, f_i, f_x_0, f_y_0, f_x_s, f_y_s, gamma):
        # Parâmetros de projeto definidos pelo usuário
        self.C = C  # Matriz que indica como as correntes fluem nas bobinas (I = CÎ)
        self.g_0 = g_0  # Dimensão do air gap (entreferro)
        self.B_b = B_b  # Densidade de campo magnético de bias
        self.r_r = r_r  # Raio do eixo
        self.f_i = f_i  # Fator que indica quanto do espaço disponível para as bases dos polos é utilizadas
        self.f_x_0 = f_x_0  # Força estática máxima em x
        self.f_y_0 = f_y_0  # Força estática máxima em y
        self.f_x_s = f_x_s  # Força variável máxima em x
        self.f_y_s = f_y_s  # Força variável máxima em x
        self.gamma = gamma  # Coeficiente que indica a organização do fluxo magnético no mancal

        # Resultados do dimensionamento
        self.A_g = None  # Área do mancal
        self.A_c = None  # Área de cobre da bobina
        self.r_j = None  # Raio externo do rotor
        self.w = None  # Largura da base do polo
        self.l = None  # Largura do mancal
        self.r_c = None  # Raio interno do contraferro
        self.r_s = None  # Raio externo do contraferro

        # Parâmetros de projeto com valores padrão
        self.alpha = 0.5  # Relação entre a densidade de fluxo magnético de bias e de saturação
        self.eta = 1  # Relação entre a área de disponível para o cobre das bobinas e a área de fato utilizada
        self.f_c = 0.5  # Razão de cobre na bobina
        self.J_max = 6e6  # Densidade de corrente máxima na bobina
        self.beta_A_c = 0.1  # Fator de segurança para a área da bobina
        self.beta_r_j = 0.1  # Fator de segurança para o raio externo do rotor
        self.beta_r_s = 0.1  # Fator de segurança para o raio do mancal

        # Constantes
        self.mu_0 = 4 * np.pi * 1e-7

        # Variáveis de controle
        self.design_done = False  # Valida se o design já foi executado
        self.log_return = None  # Guarda os logs escritos durante o design
        self.log_results = None  # Indica se os logs devem ser apresentados ou não
        self.log_level = 'DEBUG'  # Nível de detalhamento dos logs

    def log_data(self, log_level, msg):
        if self.log_results:
            if self.log_level == 'DEBUG' or (self.log_level == 'INFO' and log_level == 'INFO'):
                self.log_return += msg + '\n'
                print(msg)

    def design(self, **kwargs):
        self.log_return = ''

        # Processamento de argumentos
        self.log_results = process_kwargs(kwargs, 'log_results', False)

        # Apresentação dos parâmetros de entrada
        self.log_data('INFO', 'Parâmetros de entrada:')
        self.log_data('INFO', 'C =')
        self.log_data('INFO', f'{self.C}')
        self.log_data('INFO', f'g_0 = {self.g_0} m')
        self.log_data('INFO', f'B_b = {self.B_b} T')
        self.log_data('INFO', f'r_r = {self.r_r} m')
        self.log_data('INFO', f'f_i = {self.f_i}')
        self.log_data('INFO', f'f_x_0 = {self.f_x_0} N')
        self.log_data('INFO', f'f_y_0 = {self.f_y_0} N')
        self.log_data('INFO', f'f_x_s = {self.f_x_s} N')
        self.log_data('INFO', f'f_y_s = {self.f_y_s} N')
        self.log_data('INFO', f'gamma = {self.gamma}')
        self.log_data('INFO', f'alpha = {self.alpha}')
        self.log_data('INFO', f'eta = {self.eta}')
        self.log_data('INFO', f'f_c = {self.f_c}')
        self.log_data('INFO', f'J_max = {self.J_max * 1e-4} A/cm²')
        self.log_data('INFO', f'beta_A_c = {self.beta_A_c}')
        self.log_data('INFO', f'beta_r_j = {self.beta_r_j}')
        self.log_data('INFO', f'beta_r_s = {self.beta_r_s}')

        # Definição de variáveis
        II_base = None
        n_p = self.C.shape[0]
        B_sat = self.B_b / self.alpha

        # Computação da matriz de corrente de bias
        II_b = (self.B_b * self.g_0 / self.mu_0) * self.C[:, 2]
        self.log_data('DEBUG', '\nComputação da matriz de corrente de bias:')
        self.log_data('DEBUG', f'I_b = {np.round(II_b, decimals=5).T.tolist()[0]}T:')

        # Computação da área do air gap
        self.A_g = (1 / np.cos(np.radians(180 / n_p))) * (self.f_y_0 * self.mu_0 / B_sat ** 2)
        self.log_data('INFO', '\nComputação da área do air gap:')
        self.log_data('INFO', f'A_g = {self.A_g:.8f} m² = {self.A_g * 10 ** 4:.4f} cm²')

        # Computação das matrizes de corrente de controle
        if n_p == 8:
            II_base = self.g_0 / (4 * self.A_g * self.B_b)
        elif n_p == 6:
            II_base = self.g_0 / (3 * self.A_g * self.B_b)

        II_x = II_base * self.C[:, 0]
        II_y = II_base * self.C[:, 1]

        self.log_data('DEBUG', '\nComputação das matrizes de corrente de controle:')
        self.log_data('DEBUG', f'I_x = {np.round(II_x, decimals=5).T.tolist()[0]}T:')
        self.log_data('DEBUG', f'I_y = {np.round(II_y, decimals=5).T.tolist()[0]}T:')

        # Computação da área de cobre da bobina
        A_c_list = []

        for j in range(II_x.shape[0]):
            A_c_j = np.sqrt((II_b[j, 0] + II_x[j, 0] * self.f_x_0 + II_y[j, 0] * self.f_y_0) ** 2
                            + 0.5 * (II_x[j, 0] * self.f_x_s) ** 2
                            + 0.5 * (II_y[j, 0] * self.f_y_s) ** 2) / (self.f_c * self.J_max)
            A_c_list.append(A_c_j)

        A_c_mat = np.matrix(A_c_list)
        A_c_mat_min = A_c_mat.max()
        self.A_c = (1 + self.beta_A_c) * A_c_mat_min
        self.log_data('INFO', '\nComputação da área de cobre da bobina:')
        self.log_data('DEBUG', f'[A_c] = {np.round(((10 ** 4) * A_c_mat), decimals=5).tolist()[0]} cm²:')
        self.log_data('DEBUG', f'A_c >= {A_c_mat_min * 10 ** 4:.4f} cm²')
        self.log_data('INFO', f'A_c = {np.round(((10 ** 4) * self.A_c), decimals=5)} cm²:')

        # Computação da espessura do rotor
        theta_p = np.pi * self.f_i / n_p
        r_j_min = (self.r_r + 2 * self.gamma * self.g_0 * np.sin(theta_p)) / (1 - 2 * self.gamma * np.sin(theta_p))
        self.r_j = (1 + self.beta_r_j) * r_j_min
        self.log_data('INFO', '\nComputação da espessura do rotor:')
        self.log_data('DEBUG', f'r_j >= {r_j_min:.5f} m = {r_j_min * 100:.4f} cm')
        self.log_data('INFO', f'r_j = {self.r_j:.5f} m = {self.r_j * 100:.4f} cm')

        # Computação da largura do polo
        r_p = self.r_j + self.g_0
        self.w = 2 * r_p * np.sin(theta_p)
        self.log_data('INFO', '\nComputação da largura do polo:')
        self.log_data('INFO', f'w = {self.w:.5f} m = {self.w * 100:.4f} cm')

        # Computação da largura do mancal
        self.l = self.A_g / self.w
        self.log_data('INFO', '\nComputação da largura do mancal:')
        self.log_data('INFO', f'l = {self.l:.5f} m = {self.l * 100:.4f} cm')

        # Computação da área disponível para as bobinas
        A_v = self.eta * self.A_c
        self.r_c = (A_v / (r_p * np.tan(np.pi / n_p) - self.w / 2)) + r_p
        self.log_data('DEBUG', '\nComputação da área disponível para as bobinas:')
        self.log_data('DEBUG', f'A_v = {A_v:.6f} m² = {A_v * 10 ** 4:.4f} cm²')

        # Computação do diâmetro do mancal
        r_s_min = self.r_c + self.gamma * self.w
        self.r_s = (1 + self.beta_r_s) * r_s_min
        self.log_data('INFO', '\nComputação do diâmetro do mancal:')
        self.log_data('DEBUG', f'r_s >= {r_s_min:.5f} m = {r_s_min * 100:.5f} cm')
        self.log_data('INFO', f'r_s = {self.r_s:.5f} m = {self.r_s * 100:.5f} cm')

        self.design_done = True
        return self.A_g, self.A_c, self.r_j, self.w, self.l, self.r_c, self.r_s

    def draw(self, scale=1500, **kwargs):
        if not self.design_done:
            raise DrawWithoutDesignException('O dimensionamento precisa ser realizado antes que o MMA possa ser '
                                             'desenhado.')

        # Processamento de argumentos
        draw_axis = process_kwargs(kwargs, 'draw_axis', True)
        save_result = process_kwargs(kwargs, 'save_result', False)
        screen = process_kwargs(kwargs, 'screen', None)
        hold_draw = process_kwargs(kwargs, 'hold_draw', False)

        if 'turtle' in kwargs:
            t = kwargs['turtle']
        else:
            t = turtle

        # Dimensões do MMA
        r_j_draw = scale * self.r_j
        g_0_draw = scale * self.g_0
        r_c_draw = scale * self.r_c
        r_s_draw = scale * self.r_s
        r_r_draw = scale * self.r_r
        l_draw = scale * self.l
        w_draw = scale * self.w
        r_p_draw = r_j_draw + g_0_draw

        # Computação dos ângulos utilizados no desenho
        theta_p = np.rad2deg(2 * np.arcsin(w_draw / (2 * r_p_draw)))
        theta_pv = (45 - theta_p) / 2
        theta_c = np.rad2deg(2 * np.arcsin(w_draw / (2 * r_c_draw)))
        theta_cv = (45 - theta_c) / 2

        # Cálculo do deslocamento empregado na centralização do desenho
        delta_x = np.round(-((2.5 * r_s_draw + l_draw) / 2 - r_s_draw))

        # Inicialização do objeto Turtle utilizado no desenho
        t.clear()
        t.speed(0)
        t.pensize(3)
        t.hideturtle()
        if screen is None:
            t.tracer(0)
        else:
            screen.tracer(0)
        t.penup()
        t.goto(0, 0)
        t.setheading(0)
        t.pendown()

        # Desenho das bases dos polos
        t.penup()
        t.goto(0 + delta_x, -r_p_draw)
        pos_r_p = []
        for i in range(8):
            t.circle(r_p_draw, theta_pv)
            pos_r_p.append(t.pos())
            t.pendown()
            t.circle(r_p_draw, theta_p)
            t.penup()
            pos_r_p.append(t.pos())
            t.circle(r_p_draw, theta_pv)

        # Desenho da circunferência interna do contraferro
        t.penup()
        t.goto(0 + delta_x, -r_c_draw)
        t.pendown()
        pos_r_c = []
        for i in range(8):
            t.circle(r_c_draw, theta_cv)
            pos_r_c.append(t.pos())
            t.penup()
            t.circle(r_c_draw, theta_c)
            t.pendown()
            pos_r_c.append(t.pos())
            t.circle(r_c_draw, theta_cv)

        # Desenho das conexões entre as bases dos polos e a circunferência interna do contraferro
        for i in range(16):
            t.penup()
            t.goto(pos_r_p[i])
            t.pendown()
            t.goto(pos_r_c[i])
            t.penup()

        # Desenho da circunferência externa do contraferro
        t.penup()
        t.goto(0 + delta_x, -r_s_draw)
        t.pendown()
        t.circle(r_s_draw)

        # Desenho da circunferência interna do rotor
        t.penup()
        t.goto(0 + delta_x, -r_r_draw)
        t.pendown()
        t.circle(r_r_draw)

        # Desenho da circunferência externa do rotor (tracejada)
        t.penup()
        t.goto(0 + delta_x, -r_j_draw)
        t.pensize(1)
        pen_state = False
        for i in range(72):
            if not pen_state:
                t.pendown()
                pen_state = True
            else:
                t.penup()
                pen_state = False
            t.circle(r_j_draw, 5)

        # Desenho da vista lateral do MMA
        t.pensize(3)
        t.penup()
        t.goto(1.5 * r_s_draw + delta_x, -r_s_draw)
        t.pendown()
        t.forward(l_draw)
        t.left(90)
        t.forward(2 * r_s_draw)
        t.left(90)
        t.forward(l_draw)
        t.left(90)
        t.forward(2 * r_s_draw)

        # Desenho dos eixos x e y
        if draw_axis:
            t.pensize(1)
            t.penup()
            t.goto(-2000, 0)
            t.pendown()
            t.goto(2000, 0)
            t.penup()
            t.goto(0 + delta_x, -2000)
            t.pendown()
            t.goto(0 + delta_x, 2000)

        if screen is None:
            t.update()
        else:
            screen.update()

        # Armazenamento dos resultados
        if save_result:
            date_str = datetime.fromtimestamp(time.time()).strftime("%d-%m-%Y %H:%M:%S")
            file_name = f'files/output/mma_draw_{date_str}.eps'
            t.getscreen().getcanvas().postscript(file=file_name)

        print('Desenho concluído.')
        if hold_draw:
            t.done()
