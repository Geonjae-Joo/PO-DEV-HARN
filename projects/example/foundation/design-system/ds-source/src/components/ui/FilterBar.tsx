import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export interface FilterField {
  key: string
  label: string
  type: "text" | "select"
  options?: { label: string; value: string }[]
  placeholder?: string
}

interface FilterBarProps {
  fields: FilterField[]
  onApply: (values: Record<string, string>) => void
}

export function FilterBar({ fields, onApply }: FilterBarProps) {
  const [values, setValues] = useState<Record<string, string>>({})

  const handleChange = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleReset = () => {
    setValues({})
    onApply({})
  }

  return (
    <div className="flex flex-wrap items-end gap-2 rounded-md border bg-muted/30 p-3">
      {fields.map((field) => (
        <div key={field.key} className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground">{field.label}</label>
          {field.type === "select" ? (
            <Select
              value={values[field.key] ?? ""}
              onValueChange={(v) => handleChange(field.key, v)}
            >
              <SelectTrigger className="h-8 w-36">
                <SelectValue placeholder={field.placeholder ?? "선택"} />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              className="h-8 w-36"
              placeholder={field.placeholder ?? field.label}
              value={values[field.key] ?? ""}
              onChange={(e) => handleChange(field.key, e.target.value)}
            />
          )}
        </div>
      ))}
      <div className="flex gap-1">
        <Button size="sm" onClick={() => onApply(values)}>
          조회
        </Button>
        <Button size="sm" variant="outline" onClick={handleReset}>
          초기화
        </Button>
      </div>
    </div>
  )
}
