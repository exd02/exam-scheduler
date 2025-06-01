import json
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DataLoader:
    """
    Carrega e prepara todos os dados necessários:
    - horários (schedules)
    - alunos em recuperação (recovery_raw)
    - dias da semana (days)
    - exames em aula (exams_in_class)
    E monta:
    - subjects_by_course (disciplinas por curso, já excluindo exames em aula)
    - subjects_by_student (disciplinas por aluno, filtradas)
    - courses_by_subject (cursos por disciplina remanescente)
    - free_slots (slots livres por curso)
    - daily_slot_ranges (intervalos de slots por dia)
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.schedules: Dict[str, Dict[str, List[int]]] = {}
        self.recovery_raw: Dict[str, Dict[str, List[str]]] = {}
        self.days: List[str] = []
        self.exams_in_class: Dict[str, Dict[str, List[int]]] = {}

        self.slots_per_day: int = 0
        self.total_slots: int = 0

        # estruturas a serem preenchidas
        self.subjects_by_course: Dict[str, Set[str]] = {}
        self.subjects_by_student: Dict[Tuple[str, str], Set[str]] = {}
        self.courses_by_subject: Dict[str, List[str]] = {}
        self.free_slots: Dict[str, List[int]] = {}
        self.daily_slot_ranges: List[range] = []

        self._load_all()

    def _load_json(self, filename: str):
        path = self.base_path / filename
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_all(self):
        # Carrega arquivos brutos
        self.schedules = self._load_json("Horarios.json")
        self.recovery_raw = self._load_json("AlunosEmRecuperacao.json")
        self.days = self._load_json("Dias.json")
        self.exams_in_class = self._load_json("ExamesEmAula.json")

        # Determina quantos slots por dia e total de slots
        # (assume que todos os cursos têm a mesma estrutura de "seg", "ter", etc.)
        primeiro_curso = next(iter(self.schedules))
        self.slots_per_day = len(self.schedules[primeiro_curso]["seg"])
        self.total_slots = len(self.days) * self.slots_per_day

        # Monta subjects_by_course e subjects_by_student
        self._build_subjects()

        # Exclui disciplinas que têm exame em aula
        self._exclude_exams_in_class()

        # Reconstroi courses_by_subject
        self._build_courses_by_subject()

        # Calcula free_slots e daily_slot_ranges
        self._build_free_slots()
        self._build_daily_slot_ranges()

    def _build_subjects(self):
        # 1) Inicia subjects_by_course com todas as disciplinas dos alunos em recuperação
        self.subjects_by_course = {curso: set() for curso in self.schedules}
        self.subjects_by_student = {}

        for curso, alunos in self.recovery_raw.items():
            for aluno, disc_list in alunos.items():
                subj_set = set(disc_list)
                self.subjects_by_course[curso] |= subj_set
                self.subjects_by_student[(curso, aluno)] = subj_set.copy()

    def _exclude_exams_in_class(self):
        # 2) Para cada curso que aparece em exams_in_class, retira do subjects_by_course
        for curso, disciplinas in self.exams_in_class.items():
            if curso in self.subjects_by_course:
                to_remove = set(disciplinas.keys())
                self.subjects_by_course[curso] -= to_remove

        # 3) Atualiza subjects_by_student: cada aluno só mantém disciplinas restantes
        for (curso, aluno), subj_set in list(self.subjects_by_student.items()):
            restante = subj_set & self.subjects_by_course.get(curso, set())
            self.subjects_by_student[(curso, aluno)] = restante

    def _build_courses_by_subject(self):
        self.courses_by_subject = {}
        for curso, subj_set in self.subjects_by_course.items():
            for subj in subj_set:
                self.courses_by_subject.setdefault(subj, []).append(curso)

    def _build_free_slots(self):
        def lin(day_idx: int, period_idx: int) -> int:
            return day_idx * self.slots_per_day + period_idx

        free = {}
        for curso, agenda in self.schedules.items():
            slots = []
            for idx_dia, nome_dia in enumerate(self.days):
                for idx_per, flag in enumerate(agenda[nome_dia]):
                    if flag == 0:
                        slots.append(lin(idx_dia, idx_per))
            free[curso] = slots
        self.free_slots = free

    def _build_daily_slot_ranges(self):
        ranges = []
        for d in range(len(self.days)):
            start = d * self.slots_per_day
            end = (d + 1) * self.slots_per_day
            ranges.append(range(start, end))
        self.daily_slot_ranges = ranges
