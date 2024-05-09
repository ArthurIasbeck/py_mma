import numpy as np
from taipy.gui import Gui, notify
import os
import glob
import pandas as pd

from src.pages.index import index
from src.mma import Mma

image_amb = 'images/introducao_dimensionamento.png'

C = '1, 0, 1; 0, -1, -1; 0, 1, 1; 1, 0, -1; -1, 0, 1; 0, 1, -1; 0, -1, 1;-1 0 -1'
g_0 = 0.001
B_b = 0.6
r_r = 0.04
f_i = 0.3697
f_x_0 = 0
f_y_0 = 500
f_x_s = 75
f_y_s = 75
gamma = 1
omega_max = 1000
V = 12
alpha = 0.5
eta = 1
f_c = 0.5
J_max = 600
beta_A_c = 0.1
beta_r_j = 0.1
beta_r_s = 0.1

design_result = pd.DataFrame(columns=['Variável', 'Descrição', 'Valor'])

padding = '10px'
small_padding = '2px'
show_results = False
result_image = None
img_count = 0
file_logs = None


def download_image_end(state):
    notify(state, 'info', f'Download da imagem concluído com sucesso.')


def download_log_end(state):
    notify(state, 'info', f'Download do log concluído com sucesso.')


def button_design(state):
    notify(state, 'info', f'Iniciando processo de dimensionamento...')

    try:
        jpg_files = glob.glob(os.path.join('output/*.jpg'))

        for file_path in jpg_files:
            os.remove(file_path)

        input_C = state.C
        input_g_0 = float(state.g_0)
        input_B_b = float(state.B_b)
        input_r_r = float(state.r_r)
        input_f_i = float(state.f_i)
        input_f_x_0 = float(state.f_x_0)
        input_f_y_0 = float(state.f_y_0)
        input_f_x_s = float(state.f_x_s)
        input_f_y_s = float(state.f_y_s)
        input_gamma = float(state.gamma)
        input_omega_max = float(state.omega_max)
        input_V = float(state.V)
        input_alpha = float(state.alpha)
        input_eta = float(state.eta)
        input_f_c = float(state.f_c)
        input_J_max = float(state.J_max) * 1e4
        input_beta_A_c = float(state.beta_A_c)
        input_beta_r_j = float(state.beta_r_j)

        mma = Mma(np.matrix(input_C), input_g_0, input_B_b, input_r_r, input_f_i, input_f_x_0, input_f_y_0, input_f_x_s,
                  input_f_y_s, input_gamma, input_omega_max, input_V, input_alpha, input_eta, input_f_c, input_J_max,
                  input_beta_A_c, input_beta_r_j)

        # Dimensionamento do MMA
        _, _, _, _, _, _, _, result = mma.design(log_results=True)

        state.design_result = pd.DataFrame(columns=['Variável', 'Descrição', 'Valor'])
        design_result_df = pd.DataFrame(result)
        state.design_result = pd.concat([state.design_result, design_result_df], ignore_index=True)

        # Desenho do MMA
        mma.draw(state.img_count)

        # Apresentação dos resultadosx
        if not os.path.exists("output"):
            os.makedirs("output")

        state.result_image = f'output/mma_draw_{state.img_count}.jpg'
        state.file_logs = 'logs/py_mma.log'
        state.show_results = True
        state.img_count += 1

        notify(state, 'info', f'Processo de dimensionamento concluído com sucesso.')

    except RuntimeError as e:
        notify(state, 'error', f'Ocorreu um falha durante o processo de dimensionamento!')


gui = Gui(page=index)
