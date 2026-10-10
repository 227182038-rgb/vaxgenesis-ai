"use client";

import { useState, useEffect } from "react";

/**
 * Comments & Review Workflow (Pillar 3 — Collaboration)
 *
 * Threaded annotations on a candidate. Supports:
 *   - Inline comments
 *   - Reply threads
 *   - @mentions
 *   - Resolution status
 *   - Approval / rejection workflow
 *
 * In production, comments are synced via WebSocket for real-time
 * collaboration.
 */

interface Comment {
  id: string;
  author: string;
  author_role: string;
  body: string;
  created_at: string;
  resolved: boolean;
  replies: Comment[];
}

interface ReviewWorkflowProps {
  candidateId: string;
  candidateStatus: string;
}

const MOCK_COMMENTS: Comment[] = [
  {
    id: "1",
    author: "Dr. Sarah Chen",
    author_role: "Principal Investigator",
    body: "The HLA-A*02:01 coverage looks strong. Have we checked coverage for HLA-A*24:02 (common in Asian populations)?",
    created_at: "2026-02-15T10:30:00Z",
    resolved: false,
    replies: [
      {
        id: "1a",
        author: "Alex Kumar",
        author_role: "Bioinformatician",
        body: "Good point — adding A*24:02 to the target set and re-running. Coverage in Japan/SEA is currently 35%.",
        created_at: "2026-02-15T11:15:00Z",
        resolved: false,
        replies: [],
      },
    ],
  },
  {
    id: "2",
    author: "Dr. James O'Brien",
    author_role: "Regulatory Affairs",
    body: "Toxicity screen shows 2 flagged epitopes. These must be removed or replaced before we can proceed to IND filing.",
    created_at: "2026-02-15T14:00:00Z",
    resolved: true,
    replies: [],
  },
];

export function ReviewWorkflow({ candidateId, candidateStatus }: ReviewWorkflowProps) {
  const [comments, setComments] = useState<Comment[]>(MOCK_COMMENTS);
  const [newComment, setNewComment] = useState("");
  const [currentUser] = useState({ name: "You", role: "Scientist" });

  const handleAddComment = () => {
    if (!newComment.trim()) return;
    const comment: Comment = {
      id: Date.now().toString(),
      author: currentUser.name,
      author_role: currentUser.role,
      body: newComment,
      created_at: new Date().toISOString(),
      resolved: false,
      replies: [],
    };
    setComments([...comments, comment]);
    setNewComment("");
  };

  const handleResolve = (commentId: string) => {
    setComments(
      comments.map((c) =>
        c.id === commentId ? { ...c, resolved: !c.resolved } : c,
      ),
    );
  };

  const unresolvedCount = comments.filter((c) => !c.resolved).length;

  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="flex-between" style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 16 }}>
          Review & Comments
          {unresolvedCount > 0 && (
            <span
              className="badge badge-warning"
              style={{ marginLeft: 8, fontSize: 10 }}
            >
              {unresolvedCount} open
            </span>
          )}
        </h3>
        <div style={{ display: "flex", gap: 8 }}>
          {candidateStatus === "predicted" && (
            <>
              <button>Request Changes</button>
              <button className="primary">Approve Candidate</button>
            </>
          )}
        </div>
      </div>

      {/* Comments list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 16 }}>
        {comments.map((comment) => (
          <div
            key={comment.id}
            style={{
              padding: 12,
              background: "var(--bg-card)",
              borderRadius: 4,
              opacity: comment.resolved ? 0.6 : 1,
            }}
          >
            <div className="flex-between" style={{ marginBottom: 4 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <strong style={{ fontSize: 13 }}>{comment.author}</strong>
                <span className="badge badge-info" style={{ fontSize: 9 }}>
                  {comment.author_role}
                </span>
              </div>
              <span className="text-muted" style={{ fontSize: 11 }}>
                {new Date(comment.created_at).toLocaleString()}
              </span>
            </div>
            <p style={{ fontSize: 13, marginBottom: 8 }}>{comment.body}</p>

            {/* Replies */}
            {comment.replies.length > 0 && (
              <div
                style={{
                  marginLeft: 16,
                  borderLeft: "2px solid var(--border)",
                  paddingLeft: 12,
                  marginTop: 8,
                }}
              >
                {comment.replies.map((reply) => (
                  <div key={reply.id} style={{ marginBottom: 8 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <strong style={{ fontSize: 12 }}>{reply.author}</strong>
                      <span className="text-muted" style={{ fontSize: 10 }}>
                        {reply.author_role}
                      </span>
                    </div>
                    <p style={{ fontSize: 12, marginTop: 2 }}>{reply.body}</p>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <button
                onClick={() => handleResolve(comment.id)}
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  background: comment.resolved
                    ? "rgba(113,172,132,0.15)"
                    : "transparent",
                  borderColor: comment.resolved
                    ? "var(--success)"
                    : "var(--border)",
                }}
              >
                {comment.resolved ? "✓ Resolved" : "Resolve"}
              </button>
              <button
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  background: "transparent",
                }}
              >
                Reply
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* New comment input */}
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          onKeyDown={(e) => e.key === "Enter" && handleAddComment()}
        />
        <button className="primary" onClick={handleAddComment}>
          Post
        </button>
      </div>
    </div>
  );
}
