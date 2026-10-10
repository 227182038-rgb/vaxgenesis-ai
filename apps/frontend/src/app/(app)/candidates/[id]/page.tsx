"use client";
export default function CandidateDetailPage({ params }: { params: { id: string } }) {
  return <div><h1>Candidate: {params.id}</h1></div>;
}
