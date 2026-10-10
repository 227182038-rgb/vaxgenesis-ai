"use client";
export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  return <div><h1>Project: {params.id}</h1></div>;
}
