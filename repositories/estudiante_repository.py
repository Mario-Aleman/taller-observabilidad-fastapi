import logging
import sqlite3
from contextlib import closing

log = logging.getLogger("academico.repository")
DB = "academico.db"


class ErrorBaseDeDatos(Exception):
    """Error controlado de la capa de persistencia."""


def _conectar():
    return sqlite3.connect(DB, timeout=5)


def inicializar():
    try:
        with closing(_conectar()) as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS estudiantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    programa TEXT NOT NULL,
                    semestre INTEGER NOT NULL,
                    promedio REAL NOT NULL
                )
            """)
            conexion.commit()
    except sqlite3.Error:
        log.exception("Fallo al inicializar la base de datos")
        raise ErrorBaseDeDatos("No fue posible inicializar la base de datos")


def listar():
    try:
        with closing(_conectar()) as conexion:
            return conexion.execute(
                "SELECT id, nombre, programa, semestre, promedio FROM estudiantes"
            ).fetchall()
    except sqlite3.Error:
        log.exception("Error de BD al listar estudiantes")
        raise ErrorBaseDeDatos("Error al consultar la base de datos")


def buscar(id_estudiante):
    try:
        with closing(_conectar()) as conexion:
            return conexion.execute(
                "SELECT id, nombre, programa, semestre, promedio "
                "FROM estudiantes WHERE id = ?", (id_estudiante,)
            ).fetchone()
    except sqlite3.Error:
        log.exception("Error de BD al buscar id=%s", id_estudiante)
        raise ErrorBaseDeDatos("Error al consultar la base de datos")


def guardar(estudiante):
    try:
        with closing(_conectar()) as conexion:
            cursor = conexion.execute(
                "INSERT INTO estudiantes(nombre, programa, semestre, promedio) "
                "VALUES (?, ?, ?, ?)",
                (estudiante.nombre, estudiante.programa,
                 estudiante.semestre, estudiante.promedio))
            conexion.commit()
            return cursor.lastrowid
    except sqlite3.Error:
        log.exception("Error de BD al guardar estudiante")
        raise ErrorBaseDeDatos("Error al guardar en la base de datos")
