from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Source(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(max_length=1000)
    passages: list[str] = Field(min_length=1, max_length=8)


class ResearchPayload(StrictModel):
    sources: list[Source] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def unique_sources(self):
        if len({s.id for s in self.sources}) != len(self.sources):
            raise ValueError("Duplicate source IDs")
        if any(not p or len(p) > 8000 for s in self.sources for p in s.passages):
            raise ValueError("Passages must contain 1..8000 characters")
        return self


class ResearchRequest(StrictModel):
    contract_version: Literal["1"] = "1"
    task: Literal["researcher", "researcher.compact"]
    payload: ResearchPayload

    @model_validator(mode="after")
    def compact_boundary(self):
        sources = self.payload.sources
        if self.task == "researcher.compact" and (
            len(sources) != 1 or len(sources[0].passages) != 1
            or len(sources[0].passages[0]) > 450
        ):
            raise ValueError("Compact research requires one source and one passage <=450 characters")
        return self


class Observation(StrictModel):
    id: str = Field(min_length=1)
    claim: str
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    quote: str
    kind: Literal["observed", "inferred"]

    @model_validator(mode="after")
    def line_order(self):
        if self.end_line < self.start_line:
            raise ValueError("Reversed observation line range")
        return self


class ProfileView(StrictModel):
    observations: list[Observation] = Field(max_length=16)
    technologies: list[dict[str, Any]] = Field(default_factory=list, max_length=8)
    unknowns: list[str] = Field(default_factory=list)
    coverage_limit: str = "Only supplied observations are available."


class ResearchView(StrictModel):
    # Accepted application incidents include enrichment beyond the generation wire schema.
    incidents: list[dict[str, Any]] = Field(max_length=4)
    research_limitations: list[str]

    @model_validator(mode="after")
    def incident_identity(self):
        ids = [i.get("id") for i in self.incidents]
        if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
            raise ValueError("Accepted incidents require unique IDs")
        if any(not isinstance(i.get("source_quote"), str) for i in self.incidents):
            raise ValueError("Accepted incidents require source quotes")
        return self


class ReviewerPayload(StrictModel):
    profile: ProfileView
    research: ResearchView
    followup_answer: dict[str, Any] | None = None

    @model_validator(mode="after")
    def unique_observations(self):
        ids = [o.id for o in self.profile.observations]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate observation IDs")
        return self


class ReviewerRequest(StrictModel):
    contract_version: Literal["1"] = "1"
    task: Literal["reviewer"]
    payload: ReviewerPayload


class Evidence(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    document: str = Field(min_length=1, max_length=500)
    version_id: str = Field(min_length=1, max_length=120)
    page: int = Field(ge=1)
    text: str = Field(max_length=12000)


class VisionPayload(StrictModel):
    query: str = Field(min_length=1, max_length=2000)
    evidence: list[Evidence] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def unique_evidence(self):
        if len({e.id for e in self.evidence}) != len(self.evidence):
            raise ValueError("Duplicate evidence IDs")
        return self


class VisionRequest(StrictModel):
    contract_version: Literal["1"] = "1"
    task: Literal["vision.answer"]
    payload: VisionPayload


Request = Annotated[ResearchRequest | ReviewerRequest | VisionRequest, Field(discriminator="task")]
REQUEST = TypeAdapter(Request)
