export default function Modal({ children, onClose, className = '', align = 'center' }) {
  const cardClass = [
    'modal-card',
    className,
    align === 'left' ? 'left-align' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className={cardClass} onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  )
}
