# Dimensionamento de MMAs

## Instruções para execução

Esse projeto possibilita o dimensionamento de Mancais Magnéticos Ativos (MMAs). A execução do script `main_gui.py` promove o acesso à interface gráfica do Py MMA. Uma vez que a mesma tenha sido aberta, será possível verificar no canto superior esquerdo os campos para os parâmetros de entrada, que devem ser definidos pelo usuário. Uma vez que os parâmetros tenham sido determinados, basta que o usuário clique no botão `Executar dimensionamento` para que o dimensionamento seja realizado, os resultados sejam apresentados na caixa de texto no canto inferior esquerdo e o desenho do MMA seja apresentado à direita. 

É possível ainda realizar o dimensionamento do MMA por meio da execução do script `main.py`. Nesse caso não há uma interface gráfica e os parâmetros de projeto devem ser definidos no próprio script. No entanto, uma vez que a execução desse scrip é concluída, o desenho das vistas frontal e lateral do MMA é armazenado no diretório `files/output`. 

Para que esse projeto seja devidamente executado, recomenda-se a instalação das dependências empregadas utilizando-se o comando abaixo:

```bash
pip install -r requirements.txt
```

Em seguida, é necessário instalar o pacote TK Inter, empregado na construção dos desenhos do MMA. Para tanto, utilize o comando abaixo quando tratando-se de sistemas baseados no Ubuntu. 

```bash
sudo apt-get install python3-tk
```

As equações que basearam o desenvolvimento desse projeto podem ser verificadas em *E. H. Maslen, “Magnetic Bearing: Class Notes”, University of Virginia, Charlottesville, 2000*.

## Pacotes empregados
Esse projeto é baseado no Python 3.10.0 e emprega os pacotes listados no arquivo `requirements.txt`.

## Referências

Se o Py MMA foi útil para você de alguma forma, por favor, referencie-o conforme abaixo: 

*A. H. Iasbeck, A. A. C. Junior, e V. S. Junior, “Desenvolvimento de um programa para automatização do processo de dimensionamento de Mancais Magnéticos Ativos”, apresentado em POSMEC - Simpósio Anual de Engenharia Mecânica, Uberlândia, MG, 2023.*

Sinta-se a vontade para entrar em contato via e-mail: *arthuriasbeck@ufu.br*.
