import numpy as np
from PIL import Image, ImageDraw
import pandas as pd
from resources.log_config import logger

from exceptions.design_exception import DrawWithoutDesignException


def process_kwargs(kwargs, variable_name, default_value):
    if variable_name in kwargs:
        return kwargs[variable_name]
    else:
        return default_value


class Mma:

    def __init__(self, C, g_0, B_b, r_r, f_i, f_x_0, f_y_0, f_x_s, f_y_s, gamma, omega_max, V, alpha, eta, f_c, J_max,
                 beta_A_c, beta_r_j):
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
        self.omega_max = omega_max  # Rotação máxima do eixo sustentado pelo mancal
        self.V = V  # Tensão da fonte de alimentação que fornece corrente aos mancais
        self.alpha = alpha  # Relação entre a densidade de fluxo magnético de bias e de saturação
        self.eta = eta  # Relação entre a área de disponível para o cobre das bobinas e a área de fato utilizada
        self.f_c = f_c  # Razão de cobre na bobina
        self.J_max = J_max  # Densidade de corrente máxima na bobina
        self.beta_A_c = beta_A_c  # Fator de segurança para a área da bobina
        self.beta_r_j = beta_r_j  # Fator de segurança para o raio externo do rotor

        # Resultados do dimensionamento
        self.A_g = None  # Área do mancal
        self.A_c = None  # Área de cobre da bobina
        self.r_j = None  # Raio externo do rotor
        self.w = None  # Largura da base do polo
        self.l = None  # Largura do mancal
        self.r_c = None  # Raio interno do contraferro
        self.r_s = None  # Raio externo do contraferro
        self.df_dt_max = None  # Máxima variação temporal da força aplicada pelos mancais
        self.I_sat = None  # Corrente de saturação
        self.I_b = None  # Corrente de base
        self.N = None  # Número de voltas na espira

        # Constantes
        self.mu_0 = 4 * np.pi * 1e-7

        # Variáveis de controle
        self.design_done = False  # Valida se o design já foi executado

    def design(self, **kwargs):
        logger.info('Iniciando processo de dimensionamento...')
        result = []
        self.log_return = ''

        # Processamento de argumentos
        self.log_results = process_kwargs(kwargs, 'log_results', False)

        # Apresentação dos parâmetros de entrada
        logger.info('Parâmetros de entrada:')
        logger.info(f'C = \n{self.C}')
        logger.info(f'g_0 = {self.g_0} m')
        logger.info(f'B_b = {self.B_b} T')
        logger.info(f'r_r = {self.r_r} m')
        logger.info(f'f_i = {self.f_i}')
        logger.info(f'f_x_0 = {self.f_x_0} N')
        logger.info(f'f_y_0 = {self.f_y_0} N')
        logger.info(f'f_x_s = {self.f_x_s} N')
        logger.info(f'f_y_s = {self.f_y_s} N')
        logger.info(f'gamma = {self.gamma}')
        logger.info(f'alpha = {self.alpha}')
        logger.info(f'eta = {self.eta}')
        logger.info(f'f_c = {self.f_c}')
        logger.info(f'J_max = {self.J_max * 1e-4} A/cm²')
        logger.info(f'beta_A_c = {self.beta_A_c}')
        logger.info(f'beta_r_j = {self.beta_r_j}')

        # Definição de variáveis
        II_base = None
        n_p = self.C.shape[0]
        B_sat = self.B_b / self.alpha

        # Computação da matriz de corrente de bias
        II_b = (self.B_b * self.g_0 / self.mu_0) * self.C[:, 2]
        logger.info('Iniciando computação da matriz de corrente de bias...')
        logger.info(f'I_b = {np.round(II_b, decimals=5).T.tolist()[0]}:')

        # Computação da área do air gap
        self.A_g = (1 / np.cos(np.radians(180 / n_p))) * (self.f_y_0 * self.mu_0 / B_sat ** 2)
        logger.info('Iniciando computação da área do air gap...')
        logger.info(f'A_g = {self.A_g:.8f} m² = {self.A_g * 10 ** 4:.4f} cm²')
        result.append({'Variável': 'A_g', 'Descrição': 'Área transversal dos polos.',
                       'Valor': f'{self.A_g * 10 ** 4:.4f} cm²'})

        # Computação das matrizes de corrente de controle
        if n_p == 8:
            II_base = self.g_0 / (4 * self.A_g * self.B_b)
        elif n_p == 6:
            II_base = self.g_0 / (3 * self.A_g * self.B_b)

        II_x = II_base * self.C[:, 0]
        II_y = II_base * self.C[:, 1]

        logger.info('Iniciando computação das matrizes de corrente de controle...')
        logger.info(f'I_x = {np.round(II_x, decimals=5).T.tolist()[0]}:')
        logger.info(f'I_y = {np.round(II_y, decimals=5).T.tolist()[0]}:')

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
        logger.info('Iniciando computação da área de cobre da bobina...')
        logger.info(f'[A_c] = {np.round(((10 ** 4) * A_c_mat), decimals=5).tolist()[0]} cm²:')
        logger.info(f'A_c >= {A_c_mat_min * 10 ** 4:.4f} cm²')
        logger.info(f'A_c = {np.round(((10 ** 4) * self.A_c), decimals=5)} cm²:')
        result.append({'Variável': '[A_c]', 'Descrição': 'Área de cobre mínima de cada bobina.',
                       'Valor': f'{str(np.round(((10 ** 4) * A_c_mat), decimals=5).tolist()[0])} cm²'})
        result.append({'Variável': 'A_c', 'Descrição': 'Área de cobre das bobinas',
                       'Valor': f'{np.round(((10 ** 4) * self.A_c), decimals=5)} cm²'})

        # Computação da espessura do rotor
        theta_p = np.pi * self.f_i / n_p
        r_j_min = (self.r_r + 2 * self.gamma * self.g_0 * np.sin(theta_p)) / (1 - 2 * self.gamma * np.sin(theta_p))
        self.r_j = (1 + self.beta_r_j) * r_j_min
        logger.info('Iniciando computação da espessura do rotor...')
        logger.info(f'r_j >= {r_j_min:.5f} m = {r_j_min * 100:.4f} cm')
        logger.info(f'r_j = {self.r_j:.5f} m = {self.r_j * 100:.4f} cm')
        result.append({'Variável': 'r_j', 'Descrição': 'Espessura do rotor.', 'Valor': f'{self.r_j * 100:.4f} cm'})

        # Computação da largura do polo
        r_p = self.r_j + self.g_0
        self.w = 2 * r_p * np.sin(theta_p)
        logger.info('Iniciando computação da largura do polo...')
        logger.info(f'w = {self.w:.5f} m = {self.w * 100:.4f} cm')
        result.append({'Variável': 'w', 'Descrição': 'Largura do polo.', 'Valor': f'{self.w * 100:.4f} cm'})

        # Computação da largura do mancal
        self.l = self.A_g / self.w
        logger.info('Iniciando computação da largura do mancal...')
        logger.info(f'l = {self.l:.5f} m = {self.l * 100:.4f} cm')
        result.append({'Variável': 'l', 'Descrição': 'Largura do mancal.', 'Valor': f'{self.l * 100:.4f} cm'})

        # Computação da área disponível para as bobinas
        A_v = self.eta * self.A_c
        self.r_c = (A_v / (r_p * np.tan(np.pi / n_p) - self.w / 2)) + r_p
        logger.info('Iniciando computação da área disponível para as bobinas...')
        logger.info(f'A_v = {A_v:.6f} m² = {A_v * 10 ** 4:.4f} cm²')
        logger.info(f'r_c = {self.r_c:.6f} m = {self.r_c * 100:.4f} cm')
        result.append({'Variável': 'A_v', 'Descrição': 'Área disponível para as bobinas.',
                       'Valor': f'{A_v * 10 ** 4:.4f} cm²'})
        result.append({'Variável': 'r_c', 'Descrição': 'Raio interno do contraferro.',
                       'Valor': f'{self.r_c * 100:.4f} cm'})

        # Computação do diâmetro do mancal
        self.r_s = self.r_c + self.gamma * self.w
        logger.info('Iniciando computação do diâmetro do mancal...')
        logger.info(f'r_s = {self.r_s:.5f} m = {self.r_s * 100:.5f} cm')
        result.append({'Variável': 'r_s', 'Descrição': 'Diâmetro do mancal.', 'Valor': f'{self.r_s * 100:.5f} cm'})

        # Computação das características do bobinado
        logger.info('Iniciando computação das características do bobinado...')
        self.df_dt_max = self.f_y_0 * self.omega_max * (2 * np.pi / 60)
        L_n = (2 * self.mu_0 * self.A_g) / self.g_0
        K_in = (4 * self.mu_0 * self.A_g * np.cos(np.deg2rad(22.5))) / self.g_0 ** 2
        self.I_sat = ((L_n * self.df_dt_max) / (self.alpha * self.V * K_in))
        self.I_b = self.alpha * self.I_sat
        self.N = np.ceil((B_sat * self.g_0) / (self.mu_0 * self.I_sat))
        logger.info(f'df_dt_max = {self.df_dt_max:.2f} N/s')
        logger.info(f'I_sat = {self.I_sat:.2f} A')
        logger.info(f'I_b = {self.I_b:.2f} A')
        logger.info(f'N = {self.N}')
        result.append({'Variável': 'df_dt_max',
                       'Descrição': 'Máxima variação temporal da força aplicada pelos mancais.',
                       'Valor': f'{self.df_dt_max:.2f} N/s'})
        result.append({'Variável': 'I_sat', 'Descrição': 'Corrente de saturação.', 'Valor': f'{self.I_sat:.2f} A'})
        result.append({'Variável': 'I_b', 'Descrição': 'Corrente de base.', 'Valor': f'{self.I_b:.2f} A'})
        result.append({'Variável': 'N', 'Descrição': 'Número de voltas nas bobinas do mancal.',
                       'Valor': f'{self.N:.0f}'})

        self.design_done = True
        result_df = pd.DataFrame(result)
        logger.info('Processo de dimensionamento concluído com sucesso.')
        return self.A_g, self.A_c, self.r_j, self.w, self.l, self.r_c, self.r_s, result_df

    def draw(self, img_count, scale=100):
        if not self.design_done:
            logger.error('O dimensionamento ainda não foi realizado!')
            raise DrawWithoutDesignException('O dimensionamento precisa ser realizado antes que o MMA possa ser '
                                             'desenhado.')

        logger.info('Iniciando construção da representação gráfica do mancal...')

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
        logger.info('Representação do mancal concluída com sucesso.')
