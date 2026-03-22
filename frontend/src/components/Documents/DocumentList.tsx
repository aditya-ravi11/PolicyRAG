import React from 'react';
import type { Document } from '../../types';
import DocumentCard from './DocumentCard';

interface DocumentListProps {
  documents: Document[];
  selectedDocIds: string[];
  onToggleDoc: (id: string) => void;
  onDelete: (id: string) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedDocIds,
  onToggleDoc,
  onDelete,
}) => {
  if (documents.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-surface-500">
        No documents uploaded
      </div>
    );
  }

  return (
    <div>
      {documents.map((doc) => (
        <DocumentCard
          key={doc.id}
          document={doc}
          isSelected={selectedDocIds.includes(doc.id)}
          onToggle={() => onToggleDoc(doc.id)}
          onDelete={() => onDelete(doc.id)}
        />
      ))}
    </div>
  );
};

export default DocumentList;
