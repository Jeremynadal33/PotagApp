class Recolte:
    def __init__(self, legume, date, poids, variete = None, nombre = 0, photopath = None):
        #mail will be the unique identifier
        self.legume = legume
        self.date = date
        self.poids = poids
        self.variete = variete
        self.nombre = nombre
        self.photopath = photopath

    def get_legume(self):
        return self.legume
    def get_date(self):
        return self.date
    def get_poids(self):
        return self.poids
    def get_variete(self):
        return self.variete
    def get_nombre(self):
        return self.nombre
    def get_photopath(self):
        return self.photopath
