"""Neo4j knowledge graph client."""
from contextlib import contextmanager
from typing import Any, Generator

class KnowledgeGraph:
    """Wrapper around the Neo4j knowledge graph."""
    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                from vaxgenesis.config import settings
                self._driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                )
            except Exception:
                pass
        return self._driver

    @contextmanager
    def session(self):
        if self.driver:
            s = self.driver.session()
            try:
                yield s
            finally:
                s.close()
        else:
            yield None

    def ping(self) -> bool:
        try:
            with self.session() as s:
                return s is not None and s.run("RETURN 1").single()["1"] == 1
        except Exception:
            return False

    def add_protein(self, protein_id, name, uniprot_acc=None):
        with self.session() as s:
            if s:
                s.run("MERGE (p:Protein {id: $id}) SET p.name = $name", id=protein_id, name=name)

    def add_epitope(self, epitope_id, sequence, epitope_type, protein_id):
        with self.session() as s:
            if s:
                s.run("MERGE (e:Epitope {id: $id}) SET e.sequence = $seq", id=epitope_id, seq=sequence)

    def add_hla_binding(self, epitope_id, hla_allele, ic50_nm, prediction_method):
        with self.session() as s:
            if s:
                s.run("MERGE (h:HLA {allele: $a}) SET h.ic50 = $ic50", a=hla_allele, ic50=ic50_nm)

    def query_epitopes_for_hla(self, hla_allele, limit=100):
        with self.session() as s:
            if s:
                result = s.run("MATCH (e)-[:BINDS]->(h:HLA {allele: $a}) RETURN e LIMIT $l", a=hla_allele, l=limit)
                return [dict(r) for r in result]
        return []

knowledge_graph = KnowledgeGraph()
