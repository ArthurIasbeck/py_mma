import numpy as np
from PIL import Image, ImageDraw
import pandas as pd

from exceptions.design_exception import DrawWithoutDesignException


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
        result = []
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
        self.log_data('DEBUG', f'I_b = {np.round(II_b, decimals=5).T.tolist()[0]}:')

        # Computação da área do air gap
        self.A_g = (1 / np.cos(np.radians(180 / n_p))) * (self.f_y_0 * self.mu_0 / B_sat ** 2)
        self.log_data('INFO', '\nComputação da área do air gap:')
        self.log_data('INFO', f'A_g = {self.A_g:.8f} m² = {self.A_g * 10 ** 4:.4f} cm²')
        result.append({'Variável': 'A_g', 'Descrição': 'Área transversal dos polos.',
                       'Valor': f'{self.A_g * 10 ** 4:.4f} cm²'})

        # Computação das matrizes de corrente de controle
        if n_p == 8:
            II_base = self.g_0 / (4 * self.A_g * self.B_b)
        elif n_p == 6:
            II_base = self.g_0 / (3 * self.A_g * self.B_b)

        II_x = II_base * self.C[:, 0]
        II_y = II_base * self.C[:, 1]

        self.log_data('DEBUG', '\nComputação das matrizes de corrente de controle:')
        self.log_data('DEBUG', f'I_x = {np.round(II_x, decimals=5).T.tolist()[0]}:')
        self.log_data('DEBUG', f'I_y = {np.round(II_y, decimals=5).T.tolist()[0]}:')

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
        result.append({'Variável': '[A_c]', 'Descrição': 'Área de cobre mínima de cada bobina.',
                       'Valor': f'{str(np.round(((10 ** 4) * A_c_mat), decimals=5).tolist()[0])} cm²'})
        result.append({'Variável': 'A_c', 'Descrição': 'Área de cobre das bobinas',
                       'Valor': f'{np.round(((10 ** 4) * self.A_c), decimals=5)} cm²'})

        # Computação da espessura do rotor
        theta_p = np.pi * self.f_i / n_p  # TODO: Ajustar esse parâmetro está dando erro de numpy.float64
        r_j_min = (self.r_r + 2 * self.gamma * self.g_0 * np.sin(theta_p)) / (1 - 2 * self.gamma * np.sin(theta_p))
        self.r_j = (1 + self.beta_r_j) * r_j_min
        self.log_data('INFO', '\nComputação da espessura do rotor:')
        self.log_data('DEBUG', f'r_j >= {r_j_min:.5f} m = {r_j_min * 100:.4f} cm')
        self.log_data('INFO', f'r_j = {self.r_j:.5f} m = {self.r_j * 100:.4f} cm')
        result.append({'Variável': 'r_j', 'Descrição': 'Espessura do rotor.', 'Valor': f'{self.r_j * 100:.4f} cm'})

        # Computação da largura do polo
        r_p = self.r_j + self.g_0
        self.w = 2 * r_p * np.sin(theta_p)
        self.log_data('INFO', '\nComputação da largura do polo:')
        self.log_data('INFO', f'w = {self.w:.5f} m = {self.w * 100:.4f} cm')
        result.append({'Variável': 'w', 'Descrição': 'Largura do polo.', 'Valor': f'{self.w * 100:.4f} cm'})

        # Computação da largura do mancal
        self.l = self.A_g / self.w
        self.log_data('INFO', '\nComputação da largura do mancal:')
        self.log_data('INFO', f'l = {self.l:.5f} m = {self.l * 100:.4f} cm')
        result.append({'Variável': 'l', 'Descrição': 'Largura do mancal.', 'Valor': f'{self.l * 100:.4f} cm'})

        # Computação da área disponível para as bobinas
        A_v = self.eta * self.A_c
        self.r_c = (A_v / (r_p * np.tan(np.pi / n_p) - self.w / 2)) + r_p
        self.log_data('DEBUG', '\nComputação da área disponível para as bobinas:')
        self.log_data('DEBUG', f'A_v = {A_v:.6f} m² = {A_v * 10 ** 4:.4f} cm²')
        self.log_data('DEBUG', f'r_c = {self.r_c:.6f} m = {self.r_c * 100:.4f} cm')
        result.append({'Variável': 'A_v', 'Descrição': 'Área disponível para as bobinas.',
                       'Valor': f'{A_v * 10 ** 4:.4f} cm²'})
        result.append({'Variável': 'r_c', 'Descrição': 'Raio interno do contraferro.',
                       'Valor': f'{self.r_c * 100:.4f} cm'})

        # Computação do diâmetro do mancal
        r_s_min = self.r_c + self.gamma * self.w  # TODO: Ajustar o 
        self.r_s = (1 + self.beta_r_s) * r_s_min
        self.log_data('INFO', '\nComputação do diâmetro do mancal:')
        self.log_data('DEBUG', f'r_s >= {r_s_min:.5f} m = {r_s_min * 100:.5f} cm')
        self.log_data('INFO', f'r_s = {self.r_s:.5f} m = {self.r_s * 100:.5f} cm')
        result.append({'Variável': 'r_s', 'Descrição': 'Diâmetro do mancal.', 'Valor': f'{self.r_s * 100:.5f} cm'})

        self.design_done = True
        result_df = pd.DataFrame(result)
        return self.A_g, self.A_c, self.r_j, self.w, self.l, self.r_c, self.r_s, result_df

    def draw(self, img_count, scale=100):
        if not self.design_done:
            raise DrawWithoutDesignException('O dimensionamento precisa ser realizado antes que o MMA possa ser '
                                             'desenhado.')

        # Dimensões do MMA
        r_j_draw = scale * self.r_j * 100
        g_0_draw = scale * self.g_0 * 100
        r_c_draw = scale * self.r_c * 100
        r_s_draw = scale * self.r_s * 100
        r_r_draw = scale * self.r_r * 100
        l_draw = scale * self.l * 100
        w_draw = scale * self.w * 100
        r_p_draw = r_j_draw + g_0_draw

        # Computação dos ângulos utilizados no desenho
        theta_p = np.rad2deg(2 * np.arcsin(w_draw / (2 * r_p_draw)))
        theta_pv = (45 - theta_p) / 2
        theta_c = np.rad2deg(2 * np.arcsin(w_draw / (2 * r_c_draw)))
        theta_cv = (45 - theta_c) / 2

        # Distâncias empregadas na construção do desenho
        y_window = int(np.round(3 * r_s_draw))  # Dimensão vertical da janela
        x_window = int(np.round(y_window * (16 / 9)))  # Dimensão horizontal da janela
        distance_between_views = 0.5 * r_s_draw  # Distância entre as vistas frontal e lateral do MMA

        # Top left da caixa que contém o desenho
        draw_start_x = (x_window - (2 * r_s_draw + distance_between_views + l_draw)) / 2
        draw_start_y = 0.5 * r_s_draw

        # Definição da janela
        img = Image.new('RGB', (x_window, y_window), color=(255, 255, 255))
        d = ImageDraw.Draw(img)

        # Parâmetros empregados na construção do desenho
        width = int(round(scale / 7.5))  # Espessura da linha
        fill = (17, 28, 42)  # Cor da linha

        # Desenho das bases dos polos
        bb_start_x = draw_start_x + (r_s_draw - r_p_draw)
        bb_start_y = draw_start_y + (r_s_draw - r_p_draw)
        bb_end_x = bb_start_x + 2 * r_p_draw
        bb_end_y = bb_start_y + 2 * r_p_draw
        bounding_box = (bb_start_x, bb_start_y, bb_end_x, bb_end_y)
        start = theta_pv
        end = start + theta_p
        d.arc(bounding_box, start=start, end=end, fill=fill, width=width)
        for i in range(7):
            start = end + 2 * theta_pv
            end = start + theta_p
            d.arc(bounding_box, start=start, end=end, fill=fill, width=width)

        # Desenho dos raios internos do contraferro
        bb_start_x = draw_start_x + (r_s_draw - r_c_draw)
        bb_start_y = draw_start_y + (r_s_draw - r_c_draw)
        bb_end_x = bb_start_x + 2 * r_c_draw
        bb_end_y = bb_start_y + 2 * r_c_draw
        bounding_box = (bb_start_x, bb_start_y, bb_end_x, bb_end_y)
        start = -theta_cv
        end = start + 2 * theta_cv
        d.arc(bounding_box, start=start, end=end, fill=fill, width=width)
        for i in range(7):
            start = end + theta_c
            end = start + 2 * theta_cv
            d.arc(bounding_box, start=start, end=end, fill=fill, width=width)

        # Desenho do raio externo do mancal
        bb_start_x = draw_start_x
        bb_start_y = draw_start_y
        bb_end_x = bb_start_x + 2 * r_s_draw
        bb_end_y = bb_start_y + 2 * r_s_draw
        bounding_box = (bb_start_x, bb_start_y, bb_end_x, bb_end_y)
        d.arc(bounding_box, start=0, end=360, fill=fill, width=width)

        # Desenho dos polos
        x_0_list = []  # Lista que contém as coordenadas (x) dos pontos de partida das linhas que compõe os polos
        y_0_list = []  # Lista que contém as coordenadas (y) dos pontos de partida das linhas que compõe os polos
        zero_x = draw_start_x + r_s_draw  # Coordenada x do centro do MMA
        zero_y = draw_start_y + r_s_draw  # Coordenada y do centro do MMA
        theta = theta_pv  # Inclinação associada a alguma das linhas que compõe os polos
        x_0_list.append(zero_x + r_p_draw * np.cos(np.deg2rad(theta)))
        y_0_list.append(zero_y + r_p_draw * np.sin(np.deg2rad(theta)))
        for i in range(8):
            theta += theta_p
            x_0_list.append(zero_x + r_p_draw * np.cos(np.deg2rad(theta)))
            y_0_list.append(zero_y + r_p_draw * np.sin(np.deg2rad(theta)))
            theta += 2 * theta_pv
            x_0_list.append(zero_x + r_p_draw * np.cos(np.deg2rad(theta)))
            y_0_list.append(zero_y + r_p_draw * np.sin(np.deg2rad(theta)))

        x_f_list = []  # Lista que contém as coordenadas (x) dos pontos de chegada das linhas que compõe os polos
        y_f_list = []  # Lista que contém as coordenadas (y) dos pontos de chegada das linhas que compõe os polos
        theta = theta_cv  # Inclinação associada a alguma das linhas que compõe os polos
        x_f_list.append(zero_x + r_c_draw * np.cos(np.deg2rad(theta)))
        y_f_list.append(zero_y + r_c_draw * np.sin(np.deg2rad(theta)))
        for i in range(8):
            theta += theta_c
            x_f_list.append(zero_x + r_c_draw * np.cos(np.deg2rad(theta)))
            y_f_list.append(zero_y + r_c_draw * np.sin(np.deg2rad(theta)))
            theta += 2 * theta_cv
            x_f_list.append(zero_x + r_c_draw * np.cos(np.deg2rad(theta)))
            y_f_list.append(zero_y + r_c_draw * np.sin(np.deg2rad(theta)))

        for i in range(len(x_0_list)):
            d.line((x_0_list[i], y_0_list[i], x_f_list[i], y_f_list[i]), fill=fill, width=width)

        # Desenho do raio interno do rotor
        bb_start_x = draw_start_x + r_s_draw - r_j_draw
        bb_start_y = draw_start_y + r_s_draw - r_j_draw
        bb_end_x = bb_start_x + 2 * r_j_draw
        bb_end_y = bb_start_y + 2 * r_j_draw
        bounding_box = (bb_start_x, bb_start_y, bb_end_x, bb_end_y)
        theta = 0  # Variável auxiliar empregada no desenho dos arcos que compõe o desenho do raio interno do rotor
        step_size = 1  # Comprimento angular de cada um dos arcos que compõe o desenho do raio interno do rotor
        for i in range(int(np.floor(360 / step_size))):
            d.arc(bounding_box, start=theta, end=theta + step_size, fill=fill, width=width)
            theta += 2 * step_size

        # Desenho do raio externo do rotor
        bb_start_x = draw_start_x + r_s_draw - r_r_draw
        bb_start_y = draw_start_y + r_s_draw - r_r_draw
        bb_end_x = bb_start_x + 2 * r_r_draw
        bb_end_y = bb_start_y + 2 * r_r_draw
        bounding_box = (bb_start_x, bb_start_y, bb_end_x, bb_end_y)
        d.arc(bounding_box, start=0, end=360, fill=fill, width=width)

        # Desenho da vista lateral
        d.line((
            draw_start_x + 2 * r_s_draw + distance_between_views,
            draw_start_y,
            draw_start_x + 2 * r_s_draw + distance_between_views + l_draw,
            draw_start_y),
            fill=fill, width=width)

        d.line((
            draw_start_x + 2 * r_s_draw + distance_between_views + l_draw,
            draw_start_y,
            draw_start_x + 2 * r_s_draw + distance_between_views + l_draw,
            draw_start_y + 2 * r_s_draw),
            fill=fill, width=width)

        d.line((
            draw_start_x + 2 * r_s_draw + distance_between_views + l_draw,
            draw_start_y + 2 * r_s_draw,
            draw_start_x + 2 * r_s_draw + distance_between_views,
            draw_start_y + 2 * r_s_draw),
            fill=fill, width=width)

        d.line((
            draw_start_x + 2 * r_s_draw + distance_between_views,
            draw_start_y + 2 * r_s_draw,
            draw_start_x + 2 * r_s_draw + distance_between_views,
            draw_start_y),
            fill=fill, width=width)

        # Desenho dos eixos
        d.line((
            0,
            y_window / 2,
            x_window,
            y_window / 2),
            fill=fill, width=int(round(width / 3)))

        d.line((
            draw_start_x + r_s_draw,
            0,
            draw_start_x + r_s_draw,
            y_window),
            fill=fill, width=int(round(width / 3)))

        # Armazenamento do resultado produzido
        file_name = f'output/mma_draw_{img_count}.jpg'
        img.save(file_name)
        print('Desenho concluído.')
