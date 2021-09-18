import pandas as pd
import string


class SystemDiagnozy:

    def __init__(self, lokacja_zapisu=".", nazwa_pliku="wyniki_diagnozy"):
        self.lista_czujnikow = []
        self.tabela_diagnozy = {}
        # self.tabela_diagnozy = pd.DataFrame()

        self.lokacja_zapisu = lokacja_zapisu
        self.nazwa_pliku = nazwa_pliku

        # w nastepnej wersji wczytywana z google doca?
        self.tabela_kryteriow = {
            "CAN_max": 1,
            "CAN_min": 2,
            "ohm_out": 3,
            "real_value_out": 4,
            "delta_value_out": 5,
            "CAN_no_data": 6,
            "constant_signal":7
        }

    def dodaj_czujnik(self, nowy_czujnik):
        self.lista_czujnikow.append(nowy_czujnik)

    def diagnostyka(self, zapisz=False):

        wyniki_diagnozy = {}

        for i, czujnik in enumerate(self.lista_czujnikow):
            wyniki_diagnozy[i] = (czujnik.nazwa, czujnik.diagnoza())

        self._utworz_tabele_diagnozy2(wyniki_diagnozy)

        if zapisz:
            self._zapisz_tabele_diagnozy_v2()

        return self.tabela_diagnozy

    def _utworz_tabele_diagnozy(self, wyniki_diagnozy):

        temp_tabela_diagnozy = {}

        for nr_czujnika in wyniki_diagnozy:
            nazwa = wyniki_diagnozy[nr_czujnika][0]
            lista_bledow = [0 for kryt in self.tabela_kryteriow]

            for blad in wyniki_diagnozy[nr_czujnika][1]:
                lista_bledow[self.tabela_kryteriow[blad] - 1] = 1

            temp_tabela_diagnozy[nr_czujnika] = [nazwa]+lista_bledow

        self.tabela_diagnozy = pd.DataFrame(temp_tabela_diagnozy).T
        self.tabela_diagnozy.rename(columns={0:"nazwa_czujnika"}, inplace=True)
        self.tabela_diagnozy.rename(columns={nr_kryterium:kryterium for kryterium, nr_kryterium in self.tabela_kryteriow.items()}, inplace=True)
        self.tabela_diagnozy.index.name = "id_czujnika"
        
        
    def _utworz_tabele_diagnozy2(self, wyniki_diagnozy):

        temp_tabela_diagnozy = {}

        for nr_czujnika in wyniki_diagnozy:
            nazwa = wyniki_diagnozy[nr_czujnika][0]
            lista_bledow = [0 for kryt in self.tabela_kryteriow]

            for blad in wyniki_diagnozy[nr_czujnika][1]:
                try:
                    lista_bledow[self.tabela_kryteriow[blad] - 1] = 1
                except KeyError:
                    pass
                except IndexError:
                    pass

            temp_tabela_diagnozy[nr_czujnika] = [nazwa]+lista_bledow

        self.tabela_diagnozy = pd.DataFrame(temp_tabela_diagnozy).T
        self.tabela_diagnozy.rename(columns={0:"nazwa_czujnika"}, inplace=True)
        self.tabela_diagnozy.rename(columns={nr_kryterium:kryterium for kryterium, nr_kryterium in self.tabela_kryteriow.items()}, inplace=True)
        self.tabela_diagnozy.index.name = "id_czujnika"

    def _zapisz_tabele_diagnozy(self):

        if type(self.tabela_diagnozy) == pd.DataFrame:

            tabela_diagnozy_excel = self.tabela_diagnozy.copy()
            for kryterium in self.tabela_kryteriow:
                tabela_diagnozy_excel[kryterium] = tabela_diagnozy_excel[kryterium].map({0:"", 1:"X"})

            tabela_diagnozy_excel.to_excel(f'{self.lokacja_zapisu}/{self.nazwa_pliku}.xlsx')
            #files.download(f'{self.lokacja_zapisu}/{self.nazwa_pliku}.xlsx')

        else:
            print("Brak poprawnej tabeli diagnozy")

    def _zapisz_tabele_diagnozy_v2(self):

        if type(self.tabela_diagnozy) == pd.DataFrame:

            tabela_diagnozy_excel = self.tabela_diagnozy.copy()
            tabela_diagnozy_excel.reset_index(inplace=True)

            for kryterium in self.tabela_kryteriow:
                try:
                    tabela_diagnozy_excel[kryterium] = tabela_diagnozy_excel[kryterium].map({0:"", 1:"X"})
                except KeyError:
                    print("Błąd zapisu")
                    return

            excel_writer = pd.ExcelWriter(f'{self.lokacja_zapisu}/{self.nazwa_pliku}.xlsx', engine='xlsxwriter')

            tabela_diagnozy_excel.to_excel(excel_writer, sheet_name="diagnoza", index=False)

            workbook = excel_writer.book
            worksheet = excel_writer.sheets['diagnoza']

            format_red = workbook.add_format({'bg_color':'red', 'border':1, 'align':'center'})
            format_green = workbook.add_format({'bg_color':'#00CC00', 'border':1, 'align':'center'})

            d = dict(zip(range(25), list(string.ascii_uppercase)[1:]))

            len_df = str(len(tabela_diagnozy_excel.index) + 1)

            col1 = list(self.tabela_kryteriow.keys())[0]
            col2 = list(self.tabela_kryteriow.keys())[-1]

            excel_header1 = str(d[tabela_diagnozy_excel.columns.get_loc(col1)-1])
            excel_header2 = str(d[tabela_diagnozy_excel.columns.get_loc(col2)-1])

            rng = excel_header1 + '2:' + excel_header2 + len_df

            worksheet.conditional_format(rng, {'type': 'text',
                                                'criteria': 'begins with',
                                                'value':     'X',
                                                'format': format_red})

            worksheet.conditional_format(rng, {'type': 'blanks', 'format':  format_green})

            for i, col in enumerate(tabela_diagnozy_excel.columns):
                column_len = tabela_diagnozy_excel[col].astype(str).str.len().max()
                column_len = max(column_len, len(col)) + 2
                worksheet.set_column(i, i, column_len)

            excel_writer.save()
            #files.download(f'{self.lokacja_zapisu}/{self.nazwa_pliku}.xlsx')

        else:
            print("Brak poprawnej tabeli diagnozy")
