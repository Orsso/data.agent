import html2canvas from 'html2canvas-pro'
import { jsPDF } from 'jspdf'

/**
 * Capture the dashboard grid element and save it as a multi-page landscape PDF.
 */
export async function exportDashboardPdf(
  gridElement: HTMLElement,
  filename = 'dashboard.pdf',
): Promise<void> {
  // Hide interactive chrome and expand overflow so the full grid is captured
  gridElement.classList.add('exporting')
  const scrollParent = gridElement.closest<HTMLElement>('.overflow-auto')
  const savedOverflow = scrollParent?.style.overflow
  const savedHeight = scrollParent?.style.height
  if (scrollParent) {
    scrollParent.style.overflow = 'visible'
    scrollParent.style.height = 'auto'
  }

  try {
    const canvas = await html2canvas(gridElement, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
    })

    const pdf = new jsPDF({ orientation: 'landscape', unit: 'px', format: 'letter' })
    const pageW = pdf.internal.pageSize.getWidth()
    const pageH = pdf.internal.pageSize.getHeight()

    const imgW = pageW
    const imgH = (canvas.height * pageW) / canvas.width
    const imgData = canvas.toDataURL('image/png')

    let y = 0
    while (y < imgH) {
      if (y > 0) pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, -y, imgW, imgH)
      y += pageH
    }

    pdf.save(filename)
  } finally {
    if (scrollParent) {
      scrollParent.style.overflow = savedOverflow ?? ''
      scrollParent.style.height = savedHeight ?? ''
    }
    gridElement.classList.remove('exporting')
  }
}
