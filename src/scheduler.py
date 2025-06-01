from itertools import combinations
from ortools.sat.python import cp_model
from typing import Dict, List, Set, Tuple


class Scheduler:
    """
    Constrói o modelo CP-SAT a partir dos dados carregados em DataLoader,
    resolve o modelo e expõe o 'exam_schedule' final (lista de disciplinas
    alocadas em cada slot para cada curso).
    """

    def __init__(
        self,
        schedules: Dict[str, Dict[str, List[int]]],
        subjects_by_course: Dict[str, Set[str]],
        subjects_by_student: Dict[Tuple[str, str], Set[str]],
        courses_by_subject: Dict[str, List[str]],
        free_slots: Dict[str, List[int]],
        daily_slot_ranges: List[range],
        slots_per_day: int,
        total_slots: int,
    ):
        self.schedules = schedules
        self.subjects_by_course = subjects_by_course
        self.subjects_by_student = subjects_by_student
        self.courses_by_subject = courses_by_subject
        self.free_slots = free_slots
        self.daily_slot_ranges = daily_slot_ranges
        self.slots_per_day = slots_per_day
        self.total_slots = total_slots

        self.model = cp_model.CpModel()
        self.exam_slot: Dict[Tuple[str, str], cp_model.IntVar] = {}
        self.bool_var: Dict[Tuple[str, str, int], cp_model.BoolVar] = {}
        self.exam_schedule: Dict[str, List[List[str]]] = {}

        self._build_model()
        self._solve()

    def _build_model(self):
        # 1) Criar variáveis de decisão para cada (curso, disciplina)
        for curso in self.schedules:
            domain = cp_model.Domain.FromValues(sorted(self.free_slots[curso]))
            for subj in self.subjects_by_course.get(curso, []):
                var = self.model.NewIntVarFromDomain(domain, f"{curso}_{subj}")
                self.exam_slot[(curso, subj)] = var

        # 2) Restrição: um aluno não pode ter dois exames ao mesmo tempo
        for (curso, aluno), subj_set in self.subjects_by_student.items():
            for subj1, subj2 in combinations(sorted(subj_set), 2):
                self.model.Add(
                    self.exam_slot[(curso, subj1)] != self.exam_slot[(curso, subj2)]
                )

        # 3) Criar booleano b[(curso, subj, dia)] = 1 se exame em dia_idx
        for (curso, subj), var in self.exam_slot.items():
            for dia_idx, slot_range in enumerate(self.daily_slot_ranges):
                b = self.model.NewBoolVar(f"b_{curso}_{subj}_{dia_idx}")
                # b=1 se var ∈ slot_range, senao 0
                allowed = [(k, 1) for k in slot_range] + [
                    (k, 0)
                    for k in range(self.total_slots)
                    if k not in slot_range
                ]
                self.model.AddAllowedAssignments([var, b], allowed)
                self.bool_var[(curso, subj, dia_idx)] = b

        # 4) Cada aluno pode ter no máximo 3 exames por dia
        for (curso, aluno), subj_set in self.subjects_by_student.items():
            for dia_idx in range(len(self.daily_slot_ranges)):
                soma = sum(
                    self.bool_var[(curso, subj, dia_idx)]
                    for subj in subj_set
                )
                self.model.Add(soma <= 3)

        # 5) Sincronizar mesma disciplina entre cursos que compartilhem slot livre
        for subj, cursos in self.courses_by_subject.items():
            for c1, c2 in combinations(cursos, 2):
                intersec = set(self.free_slots[c1]) & set(self.free_slots[c2])
                if intersec:
                    self.model.Add(
                        self.exam_slot[(c1, subj)] == self.exam_slot[(c2, subj)]
                    )

        # 6) Minimizar o último slot usado
        latest = self.model.NewIntVar(0, self.total_slots - 1, "latest_slot")
        self.model.AddMaxEquality(
            latest, [var for var in self.exam_slot.values()]
        )
        self.model.Minimize(latest)

    def _solve(self):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        status = solver.Solve(self.model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError("Nenhuma solução viável encontrada")

        # 7) Montar self.exam_schedule: para cada curso, lista de listas (por slot)
        schedule = {curso: [[] for _ in range(self.total_slots)] for curso in self.schedules}
        for (curso, subj), var in self.exam_slot.items():
            slot = solver.Value(var)
            schedule[curso][slot].append(subj)

        self.exam_schedule = schedule

    def get_exam_schedule(self) -> Dict[str, List[List[str]]]:
        return self.exam_schedule
