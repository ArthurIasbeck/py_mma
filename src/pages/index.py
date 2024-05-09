index = """
# Dimensionamento de MMAs

<|{image_amb}|image|width=800px|>

## Parâmetros definidos pelo projetista

Matriz que dita como as correntes se distribuem pelas bobinas do MMA

<|part||height={small_padding}|>

<|{C}|input|label=C|multiline=True|lines_shown=1|>

<|part||height={padding}|>

Dimensão do entreferro (*air gap*)

<|part||height={small_padding}|>

<|{g_0}|input|label=g_0|>

<|part||height={padding}|>

Densidade de fluxo magnético produzida pela corrente de base

<|part||height={small_padding}|>

<|{B_b}|input|label=B_b|>

<|part||height={padding}|>

Raio do eixo

<|part||height={small_padding}|>

<|{r_r}|input|label=r_r|>

<|part||height={padding}|>

Fator que dita a relação entre o espaço ocupado pela base dos polos e o espaço disponível

<|part||height={small_padding}|>

<|{f_i}|input|label=f_i|>

<|part||height={padding}|>

Força estática máxima que o MMA deverá aplicar na direção x

<|part||height={small_padding}|>

<|{f_x_0}|input|label=f_x_0|>

<|part||height={padding}|>

Força estática máxima que o MMA deverá aplicar na direção y

<|part||height={small_padding}|>

<|{f_y_0}|input|label=f_y_0|>

<|part||height={padding}|>

Força variável máxima que o MMA deverá aplicar na direção x

<|part||height={small_padding}|>

<|{f_x_s}|input|label=f_x_s|>

<|part||height={padding}|>

Força variável máxima que o MMA deverá aplicar na direção y

<|part||height={small_padding}|>

<|{f_y_s}|input|label=f_y_s|>

<|part||height={padding}|>

Fator que dita a espessura do contraferro (e que depende da forma como os campos magnéticos fluem pelo MMA)

<|part||height={small_padding}|>

<|{gamma}|input|label=gamma|>

Máxima velocidade de rotação do eixo sustentado pelo MMA (em RPM)

<|part||height={small_padding}|>

<|{omega_max}|input|label=omega_max|>

Tensão da fonte de alimentação dos MMAs

<|part||height={small_padding}|>

<|{V}|input|label=V|>

Fator que dita a relação entre a corrente de base e a corrente de saturação

<|part||height={small_padding}|>

<|{alpha}|input|label=alpha|>

Fator que dita quanto do espaço disponível para as bobinas será de fato ocupado por elas

<|part||height={small_padding}|>

<|{eta}|input|label=eta|>

Relação entre a área do polos e a área de cobre das bobinas

<|part||height={small_padding}|>

<|{f_c}|input|label=f_c|>

Densidade de corrente máxima suportada pelo material que compõe as bobinas do mancal (x 10^4)

<|part||height={small_padding}|>

<|{J_max}|input|label=J_max|>

Fator de segurança associado à area de cobre das bobinas

<|part||height={small_padding}|>

<|{beta_A_c}|input|label=beta_A_c|>

Fator de segurança associado ao raio externo do rotor

<|part||height={small_padding}|>

<|{beta_r_j}|input|label=beta_r_j|>

<|part||height={padding}|>

<|Executar dimensionamento|button|on_action=button_design|>

<|part|render={show_results}|

## Resultados

<|{result_image}|image|width=1000px|>

<|part||height={padding}|>

<|{design_result}|table|show_all|width[Variável]=2cm|width[Descrição]=15cm|>

<|{result_image}|file_download|label=Baixar desenho|on_action=download_image_end|name=desenho.jpg|>

<|{file_logs}|file_download|label=Baixar logs|on_action=download_log_end|name=py_mma.log|>

|>

"""