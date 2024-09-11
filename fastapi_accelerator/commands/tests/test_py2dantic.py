from fastapi_accelerator.commands.py2dantic import generate_pydantic_models


def test_base_py2dantic():
    sample_data = {
        "items": [
            {
                "id": "0000",
                "premium": False,
                "name": "Python Developer",
                "department": None,
                "has_test": True,
                "response_letter_required": False,
                "area": {
                    "id": "1",
                    "name": "Москва",
                    "url": "https://api.hh.ru/areas/1",
                },
                "salary": None,
                "type": {"id": "open", "name": "Открытая"},
                "address": None,
                "response_url": None,
                "sort_point_distance": None,
                "published_at": "2024-09-04T08:27:02+0300",
                "created_at": "2024-09-04T08:27:02+0300",
                "archived": False,
                "apply_alternate_url": "https://hh.ru/applicant/vacancy_response?vacancyId=0000",
                "branding": {"type": "MAKEUP", "tariff": None},
                "show_logo_in_search": True,
                "insider_interview": None,
                "url": "https://api.hh.ru/vacancies/0000?host=hh.ru",
                "alternate_url": "https://hh.ru/vacancy/0000",
                "relations": [],
                "employer": {
                    "id": "0000",
                    "name": "nnnn",
                    "url": "https://api.hh.ru/employers/0000",
                    "alternate_url": "https://hh.ru/employer/0000",
                    "logo_urls": {
                        "90": "https://img.hhcdn.ru/ichameleon/310823.png",
                        "240": "https://img.hhcdn.ru/ichameleon/310823.png",
                        "original": "https://img.hhcdn.ru/ichameleon/310823.png",
                    },
                    "vacancies_url": "https://api.hh.ru/vacancies?employer_id=0000",
                    "accredited_it_employer": False,
                    "trusted": True,
                },
                "snippet": {
                    "requirement": "..Проводить рефакторинг, оптимизацию, осуществлять перевод...",
                },
                "contacts": None,
                "schedule": {"id": "remote", "name": "Удаленная работа"},
                "working_days": [],
                "working_time_intervals": [],
                "working_time_modes": [],
                "accept_temporary": False,
                "professional_roles": [
                    {"id": "96", "name": "Программист, разработчик"}
                ],
                "accept_incomplete_resumes": False,
                "experience": {"id": "between1And3", "name": "От 1 года до 3 лет"},
                "employment": {"id": "full", "name": "Полная занятость"},
                "adv_response_url": None,
                "is_adv_vacancy": False,
                "adv_context": None,
            },
        ],
        "found": 187,
        "pages": 2,
        "page": 1,
        "per_page": 100,
        "clusters": None,
        "arguments": None,
        "fixes": None,
        "suggests": None,
        "alternate_url": "https://hh.ru/search/vacancy?enable_snippets=true&items_on_page=100&order_by=publication_time&page=1&salary=200000&schedule=remote&text=Python+FastAPI",
    }

    assert (
        generate_pydantic_models(sample_data, depth=2, prfix_class_name="Job").strip()
        == """
class Job_ItemsItem(BaseModel):
    id: str = None
    premium: int = None
    name: str = None
    department: Any = None
    has_test: int = None
    response_letter_required: int = None
    area: Dict = None
    salary: Any = None
    type: Dict = None
    address: Any = None
    response_url: Any = None
    sort_point_distance: Any = None
    published_at: str = None
    created_at: str = None
    archived: int = None
    apply_alternate_url: str = None
    branding: Dict = None
    show_logo_in_search: int = None
    insider_interview: Any = None
    url: str = None
    alternate_url: str = None
    relations: List = None
    employer: Dict = None
    snippet: Dict = None
    contacts: Any = None
    schedule: Dict = None
    working_days: List = None
    working_time_intervals: List = None
    working_time_modes: List = None
    accept_temporary: int = None
    professional_roles: List[Dict] = None
    accept_incomplete_resumes: int = None
    experience: Dict = None
    employment: Dict = None
    adv_response_url: Any = None
    is_adv_vacancy: int = None
    adv_context: Any = None

class Job(BaseModel):
    items: List[Job_ItemsItem]
    found: int = None
    pages: int = None
    page: int = None
    per_page: int = None
    clusters: Any = None
    arguments: Any = None
    fixes: Any = None
    suggests: Any = None
    alternate_url: str = None
    """.strip()
    )


if __name__ == "__main__":
    test_base_py2dantic()
