import pandas as pd
import numpy as np


class Czujnik:
    """
    Klasa rodzic obiektow czujnik. Przeznaczona do diagnostyki czujnikow.

    Parametry inicjalizacji
    -----------------------
    CAN_series, pandas.Series
    Dane czujnika "surowe" tj. bezposrednio z danych na webx otrzymanych z XT6

    value_series, pandas Series, opcjonalny, default:None
    Dane przeliczone z czujnika, jesli nie podane seria obliczaja na podstawie metody przelicz_czujnik(). W tej klasie
    przelicz_czujnik() zwraca CAN_series

    zakres_CAN, (int, int), opcjonalny, default:(0, 32768)
    Zakres wartosci surowych CAN ktore uzyte zostana do diagnozy w metodzie sprawdz_CAN_max() i sprawdz_CAN_min()

    zakres_przeliczone, (int, int) opcjonalny, default:(-10, 120)
    Zakres wartosci przeliczonych ktore zostana uzyte do diagnozy w metodzie sprawdz_temp()

    max_delta, int, opcjonalny, default:20
    Maksymalna zmiana miedzy kolejnymi probkami danych uzyta do diagnozy w metodzie sprawdz_delta()

    nazwa, str, opcjonalny, default:""
    Opcjonalna nazwa czujnika, moze potem posluzyc do jego identyfikacji i bedzie przechowywana w zmiennej Czujnik.nazwa

    Funkcje
    -------
    przelicz_czujnik()
    Zwraca przeliczona wartosc. W przypadku tej klasy zwraca Czujnik.CAN_series

    diagnoza()
    Zwraca liste kodow bledow wg zadanych kryteriow i parametrow inicjalizacji. Jesli brak bledow zwraca pusta liste

    Funkcje diagnostyczne
    ---------------------
    sprawdz_CAN_min()
    sprawdz_CAN_max()
    sprawdz_temp()
    sprawdz_delta()
    """

    def __init__(self, CAN_series, value_series=None, zakres_CAN=(0, 32768),
                 zakres_przeliczone=(-10, 120), max_delta=20, nazwa="", dt_series=None, vel_series=None,
                 cs_przebieg_min=10, cs_procent_min=0.1):

        if CAN_series is not None:
            self.CAN_series = CAN_series
            self.brak_danych = True
        else:
            self.CAN_series = pd.Series([0])
            self.brak_danych = False

        if value_series is None and CAN_series is not None:
            self.value_series = self.przelicz_czujnik()
        elif CAN_series is None:
            self.value_series = self.CAN_series
        else:
            self.value_series = value_series

        self.CAN_min = min(zakres_CAN)
        self.CAN_max = max(zakres_CAN)
        self.przeliczone_min = min(zakres_przeliczone)
        self.przeliczone_max = max(zakres_przeliczone)
        self.max_delta = max_delta
        self.dt_series = pd.to_datetime(dt_series)
        self.vel_series = vel_series
        self.nazwa = nazwa
        self.cs_przebieg_min = cs_przebieg_min
        self.cs_procent_min = cs_procent_min

    def przelicz_czujnik(self):
        return self.CAN_series

    def diagnoza(self):

        tabela_diagnostyki = {
            "CAN_max": self.sprawdz_CAN_max(),
            "CAN_min": self.sprawdz_CAN_min(),
            "real_value_out": self.sprawdz_przeliczone(),
            "delta_value_out": self.sprawdz_delta(),
            "CAN_no_data": self.brak_danych,
            "constant_signal": self.sprawdz_constant_signal(),
        }

        lista_bledow = []

        for kod in tabela_diagnostyki:
            if not tabela_diagnostyki[kod]:
                lista_bledow.append(kod)

        return lista_bledow

    def sprawdz_CAN_min(self):

        if self.CAN_series.min() < self.CAN_min:
            return False
        else:
            return True

    def sprawdz_CAN_max(self):

        if self.CAN_series.max() > self.CAN_max:
            return False
        else:
            return True

    def sprawdz_przeliczone(self):

        if self.value_series.min() < self.przeliczone_min or self.value_series.max() > self.przeliczone_max:
            return False
        else:
            return True

    def sprawdz_delta(self):

        if self.value_series.diff().abs().max() > self.max_delta:
            return False
        else:
            return True

    def sprawdz_constant_signal(self):

        if self.dt_series is None or self.vel_series is None or not self.brak_danych:
            print(f"{self.nazwa}: brak danych dla kryterium constant_signal")
            return False

        seria_przebieg = (self.dt_series.diff().dt.total_seconds() / 3600 * self.vel_series.ffill()).round(3)

        temp_df = pd.concat([seria_przebieg, self.value_series, self.dt_series], axis=1)  # .dropna()
        temp_df = temp_df[temp_df[temp_df.columns[0]] > 0]

        aggregations = {temp_df.columns[0]: 'sum', temp_df.columns[1]: ['min', 'mean', 'max']}

        temp_df = temp_df.groupby(temp_df[temp_df.columns[2]].dt.round('H')).agg(aggregations)
        temp_df = temp_df[temp_df[temp_df.columns[0]] > self.cs_przebieg_min]

        temp_df['mean-min'] = temp_df[temp_df.columns[2]] - temp_df[temp_df.columns[1]]
        temp_df['max-mean'] = temp_df[temp_df.columns[3]] - temp_df[temp_df.columns[2]]

        temp_df['percent_val'] = self.cs_procent_min / 100 * temp_df[temp_df.columns[2]]

        if temp_df[temp_df[['mean-min', 'max-mean']].max(axis=1) < temp_df['percent_val']].size == 0:
            return True
        else:
            return False


class CzujnikTemperaturyLozysk(Czujnik):
    """
    Klasa czujnika temperatury Febi Bilstein 28334 wykorzystwanego przy lozyskach tramwaju
    Klasa dziedziczy po klasie: Czujnik

    Nadpisane metody
    ----------------

    przelicz_czujnik,
    Oblicza temperature na podstawie odczytu z danych z webx oraz wedlug charakterystyki czujnika

    """
    def przelicz_czujnik(self):

        temperatura = (-34.27 * np.log(self.CAN_series.values) + 281.81).round(1)

        return pd.Series(temperatura)


class CzujnikZawieszenia(Czujnik):

    def __init__(self, CAN_series, value_series=None, zakres_CAN=(0, 32768), zakres_przeliczone=(-40, 0),
                 max_delta=20, nazwa="", typ_wozka='napedowy', wartosc_kalibracji=0, dt_series=None, vel_series=None,
                 cs_przebieg_min=10, cs_procent_min=5):

        self.typ_wozka = typ_wozka
        self.kalibracja = wartosc_kalibracji

        # ------------------------------------------------------ #
        Czujnik.__init__(self, CAN_series, value_series=value_series, zakres_CAN=zakres_CAN,
                         zakres_przeliczone=zakres_przeliczone, max_delta=max_delta, nazwa=nazwa, dt_series=dt_series,
                         vel_series=vel_series, cs_przebieg_min=cs_przebieg_min, cs_procent_min=cs_procent_min)

    def przelicz_czujnik(self):

        if self.typ_wozka == 'napedowy':
            poziom_zawieszenia = - (20.075 * (0.5 - self.CAN_series.values / 1000) + 80.3).round(1) + self.kalibracja
        elif self.typ_wozka == 'toczny':
            poziom_zawieszenia = (20.075 * (0.5 - self.CAN_series.values / 1000)).round(1) + self.kalibracja
        else:
            poziom_zawieszenia = self.CAN_series

        return pd.Series(poziom_zawieszenia)


class CzujnikAkcelerometr(Czujnik):
    pass


class CzujnikHamulec(Czujnik):

    def przelicz_czujnik(self):
        cisnienie = (self.CAN_series * 25/1_000).round(2)
        return cisnienie


class CzujnikTemperaturySilnik(Czujnik):

    def przelicz_czujnik(self):
        temperatura = self.CAN_series.copy()
        nonan_index = ~temperatura.isna().values
        vhex_silnik = np.vectorize(self.add_2_3)
        temp_silnik_hex = vhex_silnik(temperatura[nonan_index].astype('int').values)
        temp_silnik = [int(value, 16) / 10 for value in temp_silnik_hex]

        temperatura[nonan_index] = temp_silnik

        return temperatura

    def add_2_3(self, x):
        hex_2 = self.hex_2_bajt2(x)
        hex_3 = self.hex_2_bajt3(x)
        hex_23 = hex_3 + hex_2
        return hex_23

    @staticmethod
    def hex_2_bajt2(x):
        return ('00000000' + hex(x).split('x')[-1])[-8:][2:4]

    @staticmethod
    def hex_2_bajt3(x):
        return ('00000000' + hex(x).split('x')[-1])[-8:][:2]


class CzujnikTemperaturyFalownik(Czujnik):

    def przelicz_czujnik(self):

        temperatura = self.CAN_series.copy()
        nonan_index = ~temperatura.isna().values
        vhex_falownik = np.vectorize(self.add_0_1)
        temp_falownik_hex = vhex_falownik(temperatura[nonan_index].astype('int').values)
        temp_falownik = [int(value, 16) / 10 for value in temp_falownik_hex]

        temperatura[nonan_index] = temp_falownik

        return temperatura

    def add_0_1(self, x):
        hex_0 = self.hex_2_bajt0(x)
        hex_1 = self.hex_2_bajt1(x)
        hex_01 = hex_1 + hex_0
        return hex_01

    @staticmethod
    def hex_2_bajt0(x):
        return ('00000000' + hex(x).split('x')[-1])[-8:][6:]

    @staticmethod
    def hex_2_bajt1(x):
        return ('00000000' + hex(x).split('x')[-1])[-8:][4:6]